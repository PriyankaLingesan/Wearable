"""Fig. 4 source shots: element screenshots of the app's result card (narrow viewport, 3x) for the accept, retake and upload paths.
Camera = recorded test video of SYNTHETIC frames. Run: python3 scripts/09_fig4_shots.py"""
import os, sys, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
import cv2
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server
from acquisition.server import create_app
from acquisition.synthetic import render_synthetic
OUTD = os.path.join(ROOT, "figures", "fig4_src"); os.makedirs(OUTD, exist_ok=True)
tmp = tempfile.mkdtemp()
app = create_app(os.path.join(tmp, "cap"), demo_videos=[os.path.join(ROOT, "demo", "test_feed_clean.avi"), os.path.join(ROOT, "demo", "test_feed_glare.avi")])
srv = make_server("127.0.0.1", 0, app, threaded=True); port = srv.server_port
threading.Thread(target=srv.serve_forever, daemon=True).start()
def shot(pg, name):
    pg.evaluate("document.querySelector('#result').scrollIntoView()")
    sec = pg.locator("section[aria-labelledby='h-res']"); sec.screenshot(path=os.path.join(OUTD, name))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 820, "height": 1200}, device_scale_factor=3)
    pg.goto(f"http://127.0.0.1:{port}/")
    pg.wait_for_function("document.querySelectorAll('#camSel option').length>0 && !document.querySelector('#camSel').textContent.includes('Scanning')")
    pg.select_option("#camSel", index=0); pg.click("#btnStart"); pg.wait_for_function("!document.querySelector('#btnCapture').disabled"); pg.wait_for_timeout(600)
    pg.click("#btnCapture"); pg.wait_for_selector("#cap:not([hidden])"); pg.click("#btnProcess"); pg.wait_for_selector("#result:not([hidden])", timeout=60000)
    shot(pg, "accept.png")
    pg.click("#btnStop"); pg.select_option("#camSel", index=1); pg.click("#btnStart"); pg.wait_for_function("!document.querySelector('#btnCapture').disabled")
    pg.click("#btnCapture"); pg.click("#btnProcess"); pg.wait_for_function("document.querySelector('#decision').textContent.includes('RETAKE')", timeout=60000)
    shot(pg, "retake.png"); pg.click("#btnStop")
    pg.click("#tab-up"); img, _ = render_synthetic("clean", 23, True); up = os.path.join(tmp, "close_up.png"); cv2.imwrite(up, img)
    pg.set_input_files("#file", up); pg.wait_for_selector("#cap:not([hidden])"); pg.click("#btnProcess"); pg.wait_for_selector("#result:not([hidden])", timeout=60000)
    shot(pg, "upload.png"); b.close()
srv.shutdown(); print("ok")
