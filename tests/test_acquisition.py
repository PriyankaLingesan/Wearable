"""Acquisition-subsystem tests (webcam path via OpenCV, upload path, validation, disconnect).
NOTE: the sandbox has NO physical camera. The "webcam" path is exercised with cv2.VideoCapture on a recorded test video file
(demo/test_feed_*.avi, made from SYNTHETIC frames). That tests the OpenCV capture code, but NOT a physical webcam."""
import hashlib
import io
import os
import sys
import time

import cv2
import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from acquisition.server import create_app, prepare_for_pipeline  # noqa: E402
from acquisition.synthetic import render_synthetic  # noqa: E402

V_CLEAN = os.path.join(ROOT, "demo", "test_feed_clean.avi")
V_GLARE = os.path.join(ROOT, "demo", "test_feed_glare.avi")


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    return create_app(str(tmp_path_factory.mktemp("captures")), demo_videos=[V_CLEAN, V_GLARE])


@pytest.fixture()
def client(app):
    c = app.test_client()
    yield c
    c.post("/api/camera/close")


def run_process(client, cid, risk="0.05", timeout=60):
    jid = client.post("/api/process", json=dict(capture_id=cid, risk=risk)).json["job"]
    t0 = time.time()
    while time.time() - t0 < timeout:
        j = client.get(f"/api/job/{jid}").json
        if j["state"] != "running":
            return j
        time.sleep(0.2)
    raise TimeoutError


def direct(app, cid, risk="0.05"):
    """Reference: decode the stored file and call the pipeline directly (no server code involved except the same resize rule)."""
    from simulator.app import analyse_image
    bgr, _, _ = app.store.load(cid)
    return analyse_image(prepare_for_pipeline(bgr), risk)


def open_cam(client, path):
    r = client.post("/api/camera/open", json=dict(source=path))
    assert r.status_code == 200, r.json
    t0 = time.time()
    while client.get("/api/camera/status").json["camera"]["state"] != "streaming" and time.time() - t0 < 5:
        time.sleep(0.1)


def test_no_camera_errors_are_reported(client):
    r = client.post("/api/camera/open", json=dict(source=7))
    assert r.status_code == 409 and "could not be opened" in r.json["error"]
    assert client.post("/api/camera/capture").status_code == 409
    assert client.get("/api/camera/stream").status_code == 409
    assert client.post("/api/camera/open", json=dict(source="/etc/passwd")).status_code == 400      # arbitrary paths refused


def test_webcam_path_frame_reaches_pipeline(app, client):
    open_cam(client, V_CLEAN)
    cap = client.post("/api/camera/capture").json
    assert cap["capture_id"].startswith("cam-") and cap["validation"]["ok"]
    j = run_process(client, cap["capture_id"])
    assert j["state"] == "done", j
    res, ref = j["result"], direct(app, cap["capture_id"])
    assert res["decision"] == ref["decision"] and res["text"] == ref["text"] and abs(res["p_correct"] - ref["p_correct"]) < 1e-9
    assert res["readability"] == ref["readability"]
    _, sha, path = app.store.load(cap["capture_id"])
    assert res["input"]["sha256"] == sha == hashlib.sha256(open(path, "rb").read()).hexdigest()
    assert res["text"].replace(" ", "") == "79M9RACEH916" and res["decision"] == "accept"   # content of the clean test feed (whitespace-insensitive, as in the paper)


def test_different_input_gives_different_output(app, client):
    open_cam(client, V_CLEAN); a = client.post("/api/camera/capture").json["capture_id"]
    open_cam(client, V_GLARE); b = client.post("/api/camera/capture").json["capture_id"]
    ra, rb = run_process(client, a)["result"], run_process(client, b)["result"]
    assert ra["text"] != rb["text"] and ra["decision"] == "accept" and rb["decision"] == "recapture"
    assert ra["input"]["sha256"] != rb["input"]["sha256"]


def test_upload_png_and_jpeg_reach_pipeline(app, client):
    img, gt = render_synthetic("clean", 21, True)
    for name, enc in (("hallmark.png", ".png"), ("hallmark.jpg", ".jpg")):
        ok, buf = cv2.imencode(enc, img, [cv2.IMWRITE_JPEG_QUALITY, 80] if enc == ".jpg" else [])
        up = client.post("/api/upload", data=dict(image=(io.BytesIO(buf.tobytes()), name)), content_type="multipart/form-data")
        assert up.status_code == 200, up.json
        cid = up.json["capture_id"]
        j = run_process(client, cid)
        assert j["state"] == "done", j
        ref = direct(app, cid)
        assert j["result"]["text"] == ref["text"] and j["result"]["decision"] == ref["decision"]
        assert j["result"]["input"]["sha256"] == hashlib.sha256(buf.tobytes()).hexdigest()   # exactly the uploaded bytes
    # a large (phone-camera sized) upload is downscaled by the same rule and still processed
    big = cv2.resize(img, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
    ok, buf = cv2.imencode(".jpg", big)
    cid = client.post("/api/upload", data=dict(image=(io.BytesIO(buf.tobytes()), "big.jpg")), content_type="multipart/form-data").json["capture_id"]
    r = run_process(client, cid)["result"]
    assert r["input"]["width"] == 1920 and r["input"]["processed_width"] == 640 and r["text"]


def test_webcam_and_upload_use_the_same_pipeline(app, client):
    """The same pixels must give identical results whichever acquisition path delivered them."""
    open_cam(client, V_CLEAN)
    cid_cam = client.post("/api/camera/capture").json["capture_id"]
    _, _, path = app.store.load(cid_cam)
    data = open(path, "rb").read()
    cid_up = client.post("/api/upload", data=dict(image=(io.BytesIO(data), "same.png")), content_type="multipart/form-data").json["capture_id"]
    a, b = run_process(client, cid_cam)["result"], run_process(client, cid_up)["result"]
    for k in ("decision", "text", "readability", "guidance", "guidance_cause"):
        assert a[k] == b[k]
    assert a["p_correct"] == b["p_correct"] and a["input"]["sha256"] == b["input"]["sha256"]


def test_validation_and_bad_uploads(app, client):
    assert client.post("/api/upload", data=dict(image=(io.BytesIO(b"not an image"), "x.png")), content_type="multipart/form-data").status_code == 400
    assert client.post("/api/upload", data=dict(image=(io.BytesIO(b"hello"), "notes.txt")), content_type="multipart/form-data").status_code == 400
    assert client.post("/api/upload", data={}, content_type="multipart/form-data").status_code == 400
    ok, tiny = cv2.imencode(".png", np.random.randint(0, 255, (20, 20, 3), np.uint8))
    r = client.post("/api/upload", data=dict(image=(io.BytesIO(tiny.tobytes()), "tiny.png")), content_type="multipart/form-data").json
    assert not r["validation"]["ok"] and "too small" in r["validation"]["errors"][0]
    j = run_process(client, r["capture_id"]); assert j["state"] == "error" and "too small" in j["error"]
    ok, blank = cv2.imencode(".png", np.full((200, 300, 3), 128, np.uint8))
    r = client.post("/api/upload", data=dict(image=(io.BytesIO(blank.tobytes()), "blank.png")), content_type="multipart/form-data").json
    assert not r["validation"]["ok"] and "blank" in r["validation"]["errors"][0]
    assert client.post("/api/process", json=dict(capture_id="../../etc/passwd")).status_code == 404
    assert client.post("/api/process", json=dict(capture_id="nonexistent")).status_code == 404


def test_camera_disconnect_is_detected(tmp_path):
    app = create_app(str(tmp_path), demo_videos=[V_CLEAN], loop_files=False)        # file ends -> frames stop -> "disconnected"
    c = app.test_client()
    open_cam(c, V_CLEAN)
    t0 = time.time()
    while c.get("/api/camera/status").json["camera"]["state"] == "streaming" and time.time() - t0 < 10:
        time.sleep(0.2)
    st = c.get("/api/camera/status").json["camera"]
    assert st["state"] == "disconnected" and "stopped delivering" in st["message"]
    r = c.post("/api/camera/capture"); assert r.status_code == 409 and "not available" in r.json["error"]
    c.post("/api/camera/close")


def test_mjpeg_stream_delivers_jpeg_frames(client):
    open_cam(client, V_CLEAN)
    r = client.get("/api/camera/stream", buffered=False)
    assert r.mimetype == "multipart/x-mixed-replace"
    it = iter(r.response); chunk = next(it)
    assert chunk.startswith(b"--frame") and b"\xff\xd8" in chunk
    r.close()
