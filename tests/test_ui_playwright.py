"""Browser test of the acquisition UI (headless Chromium): every control is clicked; results are compared with a direct pipeline call.
Screenshots are written to docs/screenshots/ (real screenshots of the running application). The camera shown is the TEST VIDEO FILE
source (synthetic frames), because the development sandbox has no camera."""
import os
import sys
import threading

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
pw = pytest.importorskip("playwright.sync_api")
from werkzeug.serving import make_server  # noqa: E402

from acquisition.server import create_app  # noqa: E402
from acquisition.synthetic import render_synthetic  # noqa: E402

SHOTS = os.path.join(ROOT, "docs", "screenshots")
V_CLEAN = os.path.join(ROOT, "demo", "test_feed_clean.avi")
V_GLARE = os.path.join(ROOT, "demo", "test_feed_glare.avi")


def test_ui_end_to_end(tmp_path):
    import cv2
    os.makedirs(SHOTS, exist_ok=True)
    app = create_app(str(tmp_path / "cap"), demo_videos=[V_CLEAN, V_GLARE])
    srv = make_server("127.0.0.1", 0, app, threaded=True); port = srv.server_port
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    errors = []
    try:
        with pw.sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1280, "height": 1000})
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(f"http://127.0.0.1:{port}/")
            pg.wait_for_function("document.querySelectorAll('#camSel option').length>0 && !document.querySelector('#camSel').textContent.includes('Scanning')")
            assert "Test video file: test_feed_clean.avi" in pg.inner_text("#camSel")
            assert pg.is_disabled("#btnCapture") and pg.is_disabled("#btnProcess") and pg.is_disabled("#btnRetake")
            pg.screenshot(path=os.path.join(SHOTS, "01_app_start.png"))
            # --- webcam path (test video source) ---
            pg.select_option("#camSel", index=0); pg.click("#btnStart")
            pg.wait_for_selector("#live:not([hidden])"); pg.wait_for_function("!document.querySelector('#btnCapture').disabled")
            pg.wait_for_timeout(600)
            pg.screenshot(path=os.path.join(SHOTS, "02_live_preview.png"))
            pg.click("#btnCapture"); pg.wait_for_selector("#cap:not([hidden])")
            assert "Captured" in pg.inner_text("#capMsg") and not pg.is_disabled("#btnProcess")
            pg.screenshot(path=os.path.join(SHOTS, "03_captured.png"))
            pg.click("#btnRetake"); assert pg.is_hidden("#cap") and pg.is_disabled("#btnProcess")             # Retake clears the capture
            pg.click("#btnCapture"); pg.wait_for_selector("#cap:not([hidden])")
            pg.click("#btnProcess"); pg.wait_for_selector("#result:not([hidden])", timeout=60000)
            assert pg.inner_text("#text").replace(" ", "") == "79M9RACEH916" and "ACCEPTED" in pg.inner_text("#decision")
            pg.screenshot(path=os.path.join(SHOTS, "04_result_accept_webcam_path.png"), full_page=True)
            # switch to the glare feed -> rejected with guidance
            pg.click("#btnStop"); pg.select_option("#camSel", index=1); pg.click("#btnStart"); pg.wait_for_function("!document.querySelector('#btnCapture').disabled")
            pg.click("#btnCapture"); pg.click("#btnProcess")
            pg.wait_for_function("document.querySelector('#decision').textContent.includes('RETAKE')", timeout=60000)
            assert pg.inner_text("#guide").strip() and "ACCEPTED" not in pg.inner_text("#decision")
            pg.screenshot(path=os.path.join(SHOTS, "05_result_retake_with_guidance.png"), full_page=True)
            pg.click("#btnStop")
            # --- upload path ---
            pg.click("#tab-up"); img, _ = render_synthetic("clean", 23, True); up = tmp_path / "close_up.png"; cv2.imwrite(str(up), img)
            pg.set_input_files("#file", str(up)); pg.wait_for_selector("#cap:not([hidden])")
            pg.click("#btnProcess"); pg.wait_for_selector("#result:not([hidden])", timeout=60000)
            assert pg.inner_text("#text").replace(" ", "") == "24KYJNT5AADC"
            pg.screenshot(path=os.path.join(SHOTS, "06_result_upload_path.png"), full_page=True)
            # corrupt upload -> visible error, no crash
            bad = tmp_path / "bad.png"; bad.write_bytes(b"garbage"); pg.click("#btnRetake"); pg.set_input_files("#file", str(bad)); pg.wait_for_function("document.querySelector('#upMsg').textContent.length>0")
            assert "not a decodable image" in pg.inner_text("#upMsg") and pg.is_disabled("#btnProcess")
            pg.screenshot(path=os.path.join(SHOTS, "07_upload_error.png"))
            # --- wearable-camera tab: a Python client POSTs a JPEG as the wrist unit would; the page must show the result (UI test only) ---
            import urllib.request
            pg.click("#tab-wr"); assert "PROPOSED, UNTESTED" in pg.inner_text("#pane-wr")
            jpg = cv2.imencode(".jpg", render_synthetic("clean", 21, True)[0])[1].tobytes()
            reply = urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/api/wearable/upload", data=jpg, method="POST", headers={"Content-Type": "image/jpeg"})).read().decode()
            assert reply.splitlines()[0] == "READ OK"
            pg.wait_for_function("document.querySelector('#wrMsg').textContent.includes('received')", timeout=15000)
            assert pg.inner_text("#text").replace(" ", "") == reply.splitlines()[1].replace(" ", "")
            pg.screenshot(path=os.path.join(SHOTS, "08_wearable_tab_result.png"), full_page=True)
            b.close()
    finally:
        srv.shutdown()
    assert not [e for e in errors if "favicon" not in e and "Failed to load resource" not in e], errors
