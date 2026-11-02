"""Wearable-camera interface test. A Python client stands in for the (proposed, never built) wrist unit: it POSTs JPEG bytes exactly as
the firmware would, and the REAL pipeline answers. This is NOT a test of the firmware, of a camera, or of Wi-Fi."""
import os
import re
import sys

import cv2

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from acquisition.server import create_app, prepare_for_pipeline  # noqa: E402
from acquisition.synthetic import render_synthetic  # noqa: E402

FW = os.path.join(ROOT, "hardware", "wearable_firmware", "wrist_unit", "wrist_unit.ino")


def jpeg(cond, seed):
    img, _ = render_synthetic(cond, seed, True)
    return cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()


def test_post_jpeg_returns_three_lines_and_matches_pipeline(tmp_path):
    from simulator.app import analyse_image
    app = create_app(str(tmp_path)); c = app.test_client()
    for cond, seed in [("clean", 21), ("glare", 13), ("blur", 12)]:
        data = jpeg(cond, seed)
        r = c.post("/api/wearable/upload", data=data, content_type="image/jpeg")
        assert r.status_code == 200 and r.mimetype == "text/plain"
        lines = r.get_data(as_text=True).splitlines(); assert len(lines) == 3, lines
        latest = c.get("/api/wearable/latest").json
        bgr, _, _ = app.store.load(latest["capture_id"])
        ref = analyse_image(prepare_for_pipeline(bgr), "0.05")          # same stored pixels, pipeline called directly
        head = {"accept": "READ OK", "recapture": "RETAKE", "no_mark": "NO MARK"}[ref["decision"]]
        assert lines[0] == head and lines[2] == ref["readability"]
        assert lines[1] == (ref["text"] if ref["decision"] == "accept" else ref["guidance"])
        assert latest["result"]["decision"] == ref["decision"] and latest["result"]["text"] == ref["text"]
    assert c.get("/api/wearable/latest").json["seq"] == 3


def test_same_bytes_via_upload_and_wearable_give_same_result(tmp_path):
    app = create_app(str(tmp_path)); c = app.test_client(); data = jpeg("clean", 21)
    import io, time
    up = c.post("/api/upload", data={"image": (io.BytesIO(data), "x.jpg")}, content_type="multipart/form-data").json
    jid = c.post("/api/process", json=dict(capture_id=up["capture_id"], risk="0.05")).json["job"]
    while (j := c.get(f"/api/job/{jid}").json)["state"] == "running":
        time.sleep(0.2)
    c.post("/api/wearable/upload", data=data, content_type="image/jpeg")
    w = c.get("/api/wearable/latest").json["result"]
    assert (w["decision"], w["text"], w["readability"], w["p_correct"]) == (j["result"]["decision"], j["result"]["text"], j["result"]["readability"], j["result"]["p_correct"])


def test_bad_bodies_are_rejected_with_one_text_line(tmp_path):
    c = create_app(str(tmp_path)).test_client()
    for body in (b"", b"not an image", b"\xff\xd8\xff garbage"):
        r = c.post("/api/wearable/upload", data=body, content_type="image/jpeg")
        assert r.status_code in (400, 422) and r.mimetype == "text/plain" and r.get_data(as_text=True).startswith("BAD IMAGE")
    assert c.get("/api/wearable/latest").json["seq"] == 0


def test_firmware_is_small_and_has_no_messaging_or_recognition_code():
    src = open(FW).read()
    code = re.sub(r"//.*|/\*.*?\*/", "", src, flags=re.S).lower()
    assert len([l for l in src.splitlines() if l.strip()]) < 100
    for bad in ("mqtt", "pubsub", "tesseract", "rapidocr", "randomforest", "extratrees", "isotonic", "vibrat", "haptic", "arduinojson"):
        assert bad not in code, bad
    for need in ("/api/wearable/upload", "image/jpeg", "pin_xclk = 10", "pin_pclk = 13", "pin_vsync = 38", "pin_href = 47", "pin_sccb_sda = 40", "pin_sccb_scl = 39"):
        assert need in src.lower().replace("pin_xclk = 10", "pin_xclk = 10"), need
