"""Companion application: image acquisition (laptop webcam through OpenCV, or image upload) + the REAL recognition pipeline.

  python -m acquisition.server [--port 5060] [--captures captures] [--demo-video path.avi]
        [--host 0.0.0.0]      # listen on the LAN so the wrist unit can reach it (default 127.0.0.1)

Three independent image sources feed the SAME pipeline entry point: laptop webcam (OpenCV), image upload, and the proposed wearable
camera (the wrist unit POSTs a JPEG to /api/wearable/upload and gets a 3-line text reply).

Both acquisition paths store the image on disk and then call `process_stored(capture_id)`, which reads the stored file back,
validates it, and runs simulator.app.analyse_image (quality -> localisation -> RapidOCR + Tesseract -> uncertainty features ->
ExtraTrees+isotonic rejector, Random Forest readability, rule-based guidance).  Nothing in the displayed result is scripted.
"""
import argparse
import base64
import os
import sys
import threading
import time
import uuid

import cv2
import numpy as np
from flask import Flask, Response, jsonify, render_template, request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from acquisition.camera import CameraError, CameraManager, probe_cameras  # noqa: E402
from acquisition.store import CaptureStore  # noqa: E402
from acquisition.validate import validate_frame  # noqa: E402

MAX_UPLOAD = 16 * 1024 * 1024


def thumb_b64(bgr, max_side=480):
    h, w = bgr.shape[:2]
    s = max_side / max(h, w)
    if s < 1:
        bgr = cv2.resize(bgr, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    ok, enc = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return "data:image/jpeg;base64," + base64.b64encode(enc.tobytes()).decode()


def prepare_for_pipeline(bgr, max_side=640):
    """Same size normalisation the simulator's /api/analyze has always applied (longest side <= 640 px)."""
    s = max_side / max(bgr.shape[:2])
    return cv2.resize(bgr, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else bgr


def create_app(captures_dir=None, demo_videos=(), analyse=None, loop_files=True):
    """`analyse` is injectable for tests; default is the real pipeline entry point."""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD
    store = CaptureStore(captures_dir or os.path.join(ROOT, "captures"))
    cam = CameraManager(loop_files=loop_files)
    jobs = {}
    if analyse is None:
        from simulator.app import analyse_image as analyse
    app.store, app.cam, app.jobs = store, cam, jobs
    wearable = {"seq": 0, "last": None}

    def process_stored(cid, risk):
        """THE single entry into the recognition pipeline for every acquisition path."""
        bgr, sha, path = store.load(cid)
        v = validate_frame(bgr)
        if not v["ok"]:
            raise ValueError("; ".join(v["errors"]))
        frame = prepare_for_pipeline(bgr)
        t0 = time.perf_counter()
        res = analyse(frame, risk)
        res["total_wall_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        res.pop("simulated", None)
        res["input"] = dict(capture_id=cid, file=os.path.basename(path), sha256=sha, width=int(bgr.shape[1]), height=int(bgr.shape[0]),
                            processed_width=int(frame.shape[1]), processed_height=int(frame.shape[0]), validation=v)
        res.setdefault("images", {})["input"] = thumb_b64(frame, 640)
        store.log(dict(t=time.strftime("%Y-%m-%d %H:%M:%S"), capture_id=cid, sha256=sha, decision=res["decision"], text=res["text"],
                       readability=res["readability"], p_correct=round(float(res["p_correct"]), 4), risk=risk))
        return res

    app.process_stored = process_stored

    @app.route("/")
    def index():
        from simulator.app import load_models
        S = load_models()
        return render_template("acquire.html", risk_targets=list(S["taus"].keys()),
                               demo_videos=[dict(source=p, label="Test video file: " + os.path.basename(p)) for p in demo_videos])

    @app.route("/api/health")
    def health():
        return jsonify(ok=True, camera=cam.status())

    # ---------------- camera ----------------
    @app.route("/api/cameras")
    def cameras():
        found = probe_cameras()
        found += [dict(source=p, label="Test video file: " + os.path.basename(p), test_file=True) for p in demo_videos]
        return jsonify(cameras=found, note=("" if found else "No camera detected. Connect a webcam/USB camera, or use image upload."))

    @app.route("/api/camera/open", methods=["POST"])
    def camera_open():
        j = request.get_json(silent=True) or {}
        src = j.get("source", 0)
        if isinstance(src, str) and not src.lstrip("-").isdigit():
            if src not in demo_videos:                          # only pre-registered test files can be opened by path
                return jsonify(error="unknown source"), 400
        else:
            src = int(src)
        try:
            cam.open(src)
        except CameraError as e:
            return jsonify(error=str(e), camera=cam.status()), 409
        return jsonify(camera=cam.status())

    @app.route("/api/camera/close", methods=["POST"])
    def camera_close():
        cam.close()
        return jsonify(camera=cam.status())

    @app.route("/api/camera/status")
    def camera_status():
        return jsonify(camera=cam.status())

    @app.route("/api/camera/stream")
    def camera_stream():
        if cam.state != "streaming":
            return jsonify(error="camera is not streaming"), 409
        return Response(cam.mjpeg(), mimetype="multipart/x-mixed-replace; boundary=frame")

    @app.route("/api/camera/capture", methods=["POST"])
    def camera_capture():
        try:
            fr, t = cam.capture()
        except CameraError as e:
            return jsonify(error=str(e), camera=cam.status()), 409
        cid, v = store.save_frame(fr, "webcam" if isinstance(cam.source, int) else "test-video-file")
        return jsonify(capture_id=cid, source="webcam" if isinstance(cam.source, int) else "test video file", validation=v,
                       preview=thumb_b64(fr), message=f"Captured {fr.shape[1]}x{fr.shape[0]} frame from {'webcam' if isinstance(cam.source, int) else 'TEST VIDEO FILE (not a camera)'}; saved as {cid}")

    # ---------------- upload ----------------
    @app.route("/api/upload", methods=["POST"])
    def upload():
        f = request.files.get("image")
        if f is None or not f.filename:
            return jsonify(error="no file selected"), 400
        data = f.read()
        try:
            cid, v, img = store.save_upload(data, f.filename)
        except ValueError as e:
            return jsonify(error=str(e)), 400
        return jsonify(capture_id=cid, source="upload", validation=v, preview=thumb_b64(img), message=f"Uploaded {f.filename} ({img.shape[1]}x{img.shape[0]}) saved as {cid}")

    # ---------------- processing ----------------
    def run_job(jid, cid, risk):
        j = jobs[jid]
        try:
            j["stage"] = "validating and analysing"
            res = process_stored(cid, risk)
            j.update(state="done", stage="done", result=res)
        except (KeyError, ValueError) as e:
            j.update(state="error", stage="error", error=str(e.args[0] if e.args else e))
        except Exception as e:                                   # report, never hide, a pipeline failure
            j.update(state="error", stage="error", error=f"pipeline error: {type(e).__name__}: {e}")

    # ---------------- wearable camera (PROPOSED wrist unit: one HTTP POST, reply in the response) ----------------
    @app.route("/api/wearable/upload", methods=["POST"])
    def wearable_upload():
        """Body = JPEG bytes. Runs the same pipeline as webcam/upload and replies with 3 plain-text lines for the OLED:
        <READ OK|RETAKE|NO MARK> / <transcription or hint> / <readability>.  Errors: HTTP 4xx, one text line."""
        data = request.get_data()
        try:
            cid, v, img = store.save_wearable(data)
        except ValueError as e:
            return Response(f"BAD IMAGE\n{e}\n", status=400, mimetype="text/plain")
        if not v["ok"]:
            return Response("BAD IMAGE\n" + "; ".join(v["errors"]) + "\n", status=422, mimetype="text/plain")
        try:
            res = process_stored(cid, request.args.get("risk", "0.05"))
        except Exception as e:
            return Response(f"ERROR\n{type(e).__name__}\n", status=500, mimetype="text/plain")
        head = {"accept": "READ OK", "recapture": "RETAKE", "no_mark": "NO MARK"}[res["decision"]]
        second = res["text"] if res["decision"] == "accept" else res["guidance"]
        wearable["seq"] += 1
        wearable["last"] = dict(seq=wearable["seq"], capture_id=cid, preview=thumb_b64(img), validation=v, result=res)
        return Response(f"{head}\n{second}\n{res['readability']}\n", mimetype="text/plain")

    @app.route("/api/wearable/latest")
    def wearable_latest():
        """The page polls this to show the most recent wearable capture and its result."""
        return jsonify({**(wearable["last"] or {}), "seq": wearable["seq"]})

    @app.route("/api/process", methods=["POST"])
    def process():
        j = request.get_json(silent=True) or {}
        cid, risk = j.get("capture_id"), str(j.get("risk", "0.05"))
        try:
            store.path(cid)
        except KeyError as e:
            return jsonify(error=str(e.args[0])), 404
        jid = uuid.uuid4().hex[:10]
        jobs[jid] = dict(state="running", stage="queued", capture_id=cid)
        threading.Thread(target=run_job, args=(jid, cid, risk), daemon=True).start()
        return jsonify(job=jid)

    @app.route("/api/job/<jid>")
    def job(jid):
        j = jobs.get(jid)
        if j is None:
            return jsonify(error="unknown job"), 404
        return jsonify({k: v for k, v in j.items()})

    return app


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=5060)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--captures", default=os.path.join(ROOT, "captures"))
    ap.add_argument("--demo-video", action="append", default=[], help="register a video file selectable as a TEST camera source (for machines without a camera)")
    a = ap.parse_args()
    from simulator.app import load_models
    load_models()
    app = create_app(a.captures, a.demo_video)
    print(f"Hallmark acquisition app on http://{a.host}:{a.port}")
    app.run(host=a.host, port=a.port, threaded=True, debug=False)


if __name__ == "__main__":
    main()
