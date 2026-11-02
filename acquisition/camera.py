"""Live camera acquisition with OpenCV (laptop webcam / USB camera / USB macro camera).

State machine: closed -> streaming -> (disconnected | closed).  `open()` raises CameraError if the device cannot be opened or
delivers no frame (e.g. no camera, permission denied, device busy).  If frames stop arriving while streaming (unplugged,
driver reset) the state becomes `disconnected` and capture is refused until the user re-opens a camera.

`source` is an int device index (real camera) or a str path to a video file.  The file source exists ONLY so the code path can be
tested on machines without a camera (the sandbox used for development has none); it is not a camera and the UI labels it
"test video file".
"""
import os
import threading
import time

import cv2

MAX_STALE_S = 2.0          # a capture is refused if the newest frame is older than this
FAIL_LIMIT = 8             # consecutive failed reads before declaring the camera disconnected


class CameraError(Exception):
    pass


def probe_cameras(max_index=4):
    """List device indices that open AND deliver a frame. Quiet: failures are expected on machines without cameras."""
    found = []
    for i in range(max_index + 1):
        cap = None
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ok, fr = cap.read()
                if ok and fr is not None:
                    found.append(dict(source=i, label=f"Camera {i}", width=int(fr.shape[1]), height=int(fr.shape[0])))
        except Exception:
            pass
        finally:
            if cap is not None:
                cap.release()
    return found


class CameraManager:
    def __init__(self, request_size=(1280, 720), loop_files=True, file_fps=15.0):
        self.request_size, self.loop_files, self.file_fps = request_size, loop_files, file_fps
        self._cap, self._thread, self._stop = None, None, threading.Event()
        self._lock = threading.Lock()
        self._frame, self._frame_t, self._n = None, 0.0, 0
        self.state, self.message, self.source = "closed", "no camera open", None
        self._t_open = 0.0

    # ---- lifecycle ----
    def open(self, source):
        self.close()
        is_file = isinstance(source, str)
        if is_file and not os.path.isfile(source):
            self._set("error", f"video file not found: {source}"); raise CameraError(self.message)
        try:
            cap = cv2.VideoCapture(source)
        except Exception as e:                                   # pragma: no cover (backend specific)
            self._set("error", f"could not open camera {source}: {e}"); raise CameraError(self.message)
        if not cap.isOpened():
            cap.release()
            self._set("error", f"camera {source} could not be opened (not connected, in use by another application, or permission denied)")
            raise CameraError(self.message)
        if not is_file and self.request_size:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.request_size[0]); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.request_size[1])
        ok, fr = cap.read()
        if not ok or fr is None:
            cap.release()
            self._set("error", f"camera {source} opened but delivered no frame"); raise CameraError(self.message)
        self._cap, self.source = cap, source
        self._stop.clear()
        with self._lock:
            self._frame, self._frame_t, self._n = fr, time.time(), 1
        self._t_open = time.time()
        self._set("streaming", "live preview running")
        self._thread = threading.Thread(target=self._reader, args=(is_file,), daemon=True)
        self._thread.start()

    def close(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._cap is not None:
            self._cap.release()
        self._cap, self._thread = None, None
        with self._lock:
            self._frame = None
        self._set("closed", "no camera open"); self.source = None

    def _set(self, state, msg):
        self.state, self.message = state, msg

    def _reader(self, is_file):
        fails = 0
        period = 1.0 / self.file_fps
        while not self._stop.is_set():
            t0 = time.time()
            ok, fr = False, None
            try:
                ok, fr = self._cap.read()
            except Exception:
                ok = False
            if not ok or fr is None:
                if is_file and self.loop_files and fails == 0:
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0); fails += 1; continue
                fails += 1
                if fails >= FAIL_LIMIT:
                    self._set("disconnected", "camera stopped delivering frames (disconnected, unplugged or driver error); re-open a camera")
                    return
                time.sleep(0.1); continue
            fails = 0
            with self._lock:
                self._frame, self._frame_t, self._n = fr, time.time(), self._n + 1
            if is_file:
                time.sleep(max(0.0, period - (time.time() - t0)))

    # ---- access ----
    def latest(self):
        with self._lock:
            return (None, 0.0) if self._frame is None else (self._frame.copy(), self._frame_t)

    def capture(self):
        """Return (bgr, timestamp) of the newest frame. Raises CameraError unless the camera is streaming with a fresh frame."""
        if self.state != "streaming":
            raise CameraError(f"camera not available ({self.state}): {self.message}")
        fr, t = self.latest()
        if fr is None or time.time() - t > MAX_STALE_S:
            raise CameraError("no fresh frame from the camera (it may have stalled); retry or re-open the camera")
        return fr, t

    def status(self):
        fr, t = self.latest()
        d = dict(state=self.state, message=self.message, source=self.source, frames=self._n)
        if fr is not None:
            d.update(width=int(fr.shape[1]), height=int(fr.shape[0]), frame_age_s=round(time.time() - t, 2))
            if self._t_open and self.state == "streaming":
                d["fps"] = round(self._n / max(1e-6, time.time() - self._t_open), 1)
        return d

    def mjpeg(self, quality=75):
        """Generator of multipart MJPEG for the browser preview. Ends when the camera stops streaming."""
        last = -1
        while self.state == "streaming":
            fr, _ = self.latest()
            if fr is None or self._n == last:
                time.sleep(0.03); continue
            last = self._n
            ok, enc = cv2.imencode(".jpg", fr, [cv2.IMWRITE_JPEG_QUALITY, quality])
            if ok:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + enc.tobytes() + b"\r\n"
            time.sleep(0.03)
