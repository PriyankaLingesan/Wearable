"""Revision-5 diagrams (editable source). Run: python3 diagrams/src/new_diagrams.py
Status badges say what exists:  IMPLEMENTED (code exists)  TESTED (automated test passes)  SIMULATED (Wokwi/emulator)
PROPOSED (design only, not built)  TEST ONLY (test video file standing in for a camera)  NOT TESTED."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dlib import Canvas, PURPLE


def wrist_unit_layout():
    c = Canvas(9.0, 6.0)
    c.text(4.5, 5.78, "Wrist-worn camera unit layout (PROPOSED design: not built, not simulated as a whole)", fs=9.2, bold=True)
    c.section(0.1, 0.9, 5.2, 4.6, "Electrical block layout (XIAO ESP32S3 Sense, single board)", "A")
    c.box(0.3, 3.9, 1.7, 0.9, "USB-C 5 V\n(power bank)", "gray", badge="PROPOSED")
    c.box(2.5, 2.2, 1.8, 2.6, "XIAO ESP32S3\nSense\n8 MB PSRAM\nWi-Fi, HTTP POST,\nJPEG capture\n(no OCR on device)", "A", badge="PROPOSED")
    c.box(0.3, 2.9, 1.7, 0.8, "Camera: proposed\nOV5640 AF (kit may\nship OV3660)", "A", badge="PROPOSED")
    c.box(0.3, 1.8, 1.7, 0.9, "White LED +\nNPN driver\n(ILLUMINATION)", "led", badge="PROPOSED")
    c.box(2.5, 0.95, 1.8, 1.0, "OLED SSD1306\n128x64, I2C\nstatus, result", "C", badge="PROPOSED")
    c.box(4.5, 3.9, 0.7, 0.8, "Button", "A", fs=7)
    c.arrow((2.0, 4.35), (2.5, 4.35), None); c.text(2.25, 4.55, "5 V", fs=6.0)
    c.arrow((2.0, 3.3), (2.5, 3.3), None); c.text(2.25, 3.5, "DVP/SCCB", fs=5.6)
    c.arrow((2.0, 2.25), (2.5, 2.6), None); c.text(2.1, 2.05, "D0", fs=5.6)
    c.arrow((3.4, 2.2), (3.4, 1.95), None); c.text(3.95, 2.07, "I2C D4/D5", fs=6.0)
    c.arrow((4.5, 4.3), (4.3, 4.3), None); c.text(4.85, 4.85, "D1", fs=6.0)
    c.text(2.7, 0.65, "Camera GPIOs are fixed by the Sense board. Wokwi mirrors only the\nbutton, LED and OLED (no camera part exists). No board was built.", fs=6.4, color="#8a6a10")
    c.section(5.5, 0.9, 3.4, 4.6, "Indicative physical placement (not to scale)", "C")
    ax = c.ax
    from matplotlib.patches import FancyBboxPatch, Rectangle
    ax.add_patch(Rectangle((5.75, 3.6), 2.9, 0.5, fc="#2b2a27", ec="none")); ax.add_patch(Rectangle((5.75, 1.5), 2.9, 0.5, fc="#2b2a27", ec="none"))
    ax.add_patch(FancyBboxPatch((6.1, 2.0), 2.2, 1.6, boxstyle="round,pad=0,rounding_size=0.15", fc="#1b1d21", ec="#3b3d42", lw=2))
    ax.add_patch(Rectangle((6.35, 2.7), 1.1, 0.6, fc="#000", ec="#777")); c.text(6.9, 3.0, "OLED", fs=6.5, color="#f5c542")
    ax.add_patch(Rectangle((8.3, 2.9), 0.12, 0.45, fc="#777", ec="none"))
    ax.add_patch(plt_circle(6.55, 2.3, 0.12, "#e8f0ff")); ax.add_patch(plt_circle(7.45, 2.3, 0.12, "#e8f0ff")); ax.add_patch(plt_circle(7.0, 2.3, 0.17, "#0b0c0e", "#999"))
    c.text(7.0, 2.52, "front edge: LED  camera  LED", fs=6.0, color="#ddd")
    c.arrow((7.0, 2.0), (7.0, 1.3), None, color="#B7791F"); c.text(7.0, 1.12, "faces the jewellery\n(about 30 mm, design target)", fs=6.4, color="#8a6a10")
    c.text(7.2, 4.5, "Wrist strap, top view of the enclosure", fs=6.8)
    c.text(7.2, 5.05, "Push button on the right side. The camera\nis the sensor; the LED only illuminates.", fs=6.6, color="#333")
    c.save("wrist_unit_layout")


def plt_circle(x, y, r, fc, ec="#999"):
    from matplotlib.patches import Circle
    return Circle((x, y), r, fc=fc, ec=ec, lw=1)


def acquisition_workflow():
    c = Canvas(9.0, 6.6)
    c.text(4.5, 6.4, "Camera sensing and image-acquisition workflow", fs=9.4, bold=True)
    c.section(0.1, 4.45, 8.8, 1.75, "Image sources (three paths into the same pipeline)", "B")
    c.box(0.3, 4.6, 2.7, 1.2, "Laptop webcam / USB camera\ncv2.VideoCapture, live MJPEG preview,\ncapture button; handles no camera, busy,\ndisconnect, stale frame\n(tested with a test video file only)", "B", badge="IMPLEMENTED", fs=6.6)
    c.box(3.2, 4.6, 2.5, 1.2, "Image upload\nPNG / JPEG / BMP / WebP / TIFF\nclose-up photograph, 16 MB max\n(fallback for macro images)", "B", badge="TESTED", fs=6.8)
    c.box(5.9, 4.6, 2.85, 1.2, "Proposed wrist camera (XIAO ESP32S3\nSense, camera module TBC) -> JPEG -> HTTP POST\n/api/wearable/upload. Receiver tested;\nfirmware compiled in Wokwi only", "A", ls="--", badge="PROPOSED", fs=6.8)
    c.box(0.3, 3.35, 8.45, 0.6, "Store on disk: PNG for webcam frames, original bytes for uploads; sha256 recorded", "B", fs=7.4, bold_first=False)
    for x in (1.65, 4.45, 7.3):
        c.arrow((x, 4.6), (x, 3.95), None)
    c0, c1, c2, c3 = 0.3, 2.5, 4.7, 6.9; w = 1.85
    c.box(c0, 2.05, w, 0.95, "Image validation\ndecodable, 64..8000 px,\nnot blank; warns if dark,\nsaturated, low-res", "B", fs=6.6)
    c.box(c1, 2.05, w, 0.95, "Captured-image preview\ncapture confirmation\nRETAKE discards it", "B", fs=6.8, badge="TESTED")
    c.box(c2, 2.05, w, 0.95, "Process image\n(webcam / upload: user\npresses; wearable: auto)", "B", fs=6.4)
    c.box(c3, 2.05, w, 0.95, "process_stored(id)\nread file back from\ndisk, resize longest\nside to <= 640 px", "B", fs=6.6)
    c.arrow((c0 + w / 2, 3.35), (c0 + w / 2, 3.0), None)
    for xa, xb in ((c0 + w, c1), (c1 + w, c2), (c2 + w, c3)):
        c.arrow((xa, 2.525), (xb, 2.525), None)
    c.box(c0, 0.45, w, 0.95, "Rejected with a\nreason; never\nprocessed", "gray", fs=6.8)
    c.arrow((c0 + w / 2, 2.05), (c0 + w / 2, 1.4), "invalid", lx=0.35, color="#C62828", fs=6.4, ls="--")
    c.box(c1, 0.45, w, 0.95, "Result in UI\n(wearable: 3-line\ntext reply to OLED)", "C", fs=6.8)
    c.box(c2, 0.45, 4.05, 0.95, "Existing pipeline: analyse_image()\nquality -> localisation -> ROI -> RapidOCR + Tesseract ->\nuncertainty -> readability + calibrated rejection -> guidance", "rej", fs=6.6, badge="IMPLEMENTED")
    c.arrow((c3 + w / 2, 2.05), (c3 + w / 2, 1.4), "valid", lx=0.3, fs=6.4)
    c.arrow((c2, 0.925), (c1 + w, 0.925), None)
    c.save("acquisition_workflow")


def companion_pipeline():
    c = Canvas(9.0, 5.6)
    c.text(4.5, 5.4, "Companion processing pipeline (implemented, Python)", fs=9.4, bold=True)
    xs = [0.2, 2.45, 4.7, 6.95]; w = 1.85; h = 1.05
    c.section(0.1, 3.3, 8.8, 1.85, "Frame to ROI", "B")
    c.box(xs[0], 3.45, w, h, "Image validation\n+ resize <= 640 px", "B", n=1); c.box(xs[1], 3.45, w, h, "Image-quality\nassessment\n21 features (frame + ROI)", "B", n=2)
    c.box(xs[2], 3.45, w, h, "Hallmark\nlocalisation\ncontour method", "B", n=3); c.box(xs[3], 3.45, w, h, "ROI extraction\nraw gray (primary)\nred channel (secondary)", "B", n=4)
    for i in range(3): c.arrow((xs[i] + w, 3.975), (xs[i + 1], 3.975))
    c.section(0.1, 0.1, 8.8, 3.05, "Recognition, readability and decision", "B")
    c.box(xs[3], 1.95, w, h, "OCR engine A\nRapidOCR on raw\ngray ROI (primary)", "B", n=5); c.box(xs[3], 0.35, w, h, "OCR engine B\nTesseract on red-\nchannel ROI", "B", n=5)
    c.arrow((xs[3] + w / 2, 3.45), (xs[3] + w / 2, 3.0), None); c.text(xs[3] + w / 2 + 0.55, 3.22, "parallel", fs=6.2)
    c.box(xs[2], 1.15, w, 1.1, "OCR-uncertainty\nfeatures: confidences,\nA/B disagreement,\nlengths", "B", n=6)
    c.arrow((xs[3], 2.5), (xs[2] + w, 2.0), None); c.arrow((xs[3], 0.9), (xs[2] + w, 1.4), None)
    c.box(xs[1], 1.95, w, 0.8, "Readability class\nRandom Forest on\nquality features", "B", n=7)
    c.box(xs[1], 0.45, w, 1.35, "Calibrated rejection\nExtraTrees (quality +\nOCR uncertainty)\n+ isotonic -> p", "rej", n=8)
    c.arrow((xs[2], 1.7), (xs[1] + w, 1.2), None); c.arrow((xs[2], 2.1), (xs[1] + w, 2.35), None, ls="--", lw=1.0)
    c.text(xs[2] - 0.2, 2.45, "quality feats", fs=5.8, color="#555")
    c.box(xs[0], 1.0, w, 1.4, "Decision: p >= tau (UCB,\n5 % risk target)\naccept / recapture /\nno_mark + rule-based\nrecapture guidance", "B", n=9)
    c.arrow((xs[1], 1.1), (xs[0] + w, 1.5), None); c.arrow((xs[1], 2.35), (xs[0] + w, 2.15), None, lw=1.0)
    c.text(4.5, 0.2, "Gradient Boosting = compared alternative to the Random Forest (not deployed).", fs=6.4, color="#2F5D8C")
    c.save("companion_pipeline")


def ocr_ml_workflow():
    c = Canvas(9.0, 4.8)
    c.text(4.5, 4.6, "OCR and machine-learning workflow: which model does what", fs=9.4, bold=True)
    c.box(0.15, 2.9, 1.5, 1.0, "ROI image\n(gray / red\nchannel)", "B")
    c.box(2.0, 3.3, 2.0, 0.75, "RapidOCR (primary)\non raw gray ROI", "B"); c.box(2.0, 2.2, 2.0, 0.75, "Tesseract (secondary)\non red-channel ROI", "B")
    c.arrow((1.65, 3.5), (2.0, 3.65), None); c.arrow((1.65, 3.2), (2.0, 2.6), None)
    c.box(4.4, 2.65, 1.9, 1.0, "Feature vector\nOCR uncertainty\n(confidences, A/B\ndisagreement) + quality", "B", fs=6.8); c.arrow((4.0, 3.65), (4.4, 3.3), "text, conf", fs=6, ly=0.18); c.arrow((4.0, 2.6), (4.4, 3.0), None)
    c.box(4.4, 3.8, 1.9, 0.5, "Quality features (21)", "B", fs=7); c.arrow((5.35, 3.8), (5.35, 3.65), None)
    c.box(6.65, 3.3, 2.2, 0.85, "Random Forest\nreadability class\n(quality features only)", "B"); c.arrow((6.3, 4.05), (6.65, 3.9), None)
    c.box(6.65, 2.2, 2.2, 0.85, "Gradient Boosting\ncompared alternative\n(NOT deployed)", "gray", ls="--"); c.arrow((6.3, 4.05), (6.65, 2.9), None, ls="--", lw=1.0)
    c.box(2.0, 0.55, 2.3, 1.0, "ExtraTrees base model\non quality + OCR\nuncertainty (S5)", "rej"); c.box(4.7, 0.55, 2.0, 1.0, "Isotonic calibration\n(fit on out-of-fold\nscores) -> p", "rej")
    c.box(7.0, 0.55, 1.85, 1.0, "accept if p >= tau\n(Clopper-Pearson\nUCB threshold)", "rej")
    c.arrow((5.35, 2.65), (3.15, 1.55), None); c.arrow((4.3, 1.05), (4.7, 1.05), None); c.arrow((6.7, 1.05), (7.0, 1.05), None)
    c.text(1.0, 1.05, "Trained on the 1,440\nsynthetic images\n(item-level split)", fs=6.6, color="#555")
    c.save("ocr_ml_workflow")


def comm_architecture():
    c = Canvas(9.0, 5.6)
    c.text(4.5, 5.4, "Wearable camera to companion: one HTTP request over Wi-Fi", fs=9.4, bold=True)
    c.section(0.1, 3.0, 2.8, 2.15, "Wrist unit (XIAO ESP32S3 Sense)", "A")
    c.box(0.25, 3.15, 2.5, 1.35, "Button -> LED on ->\nJPEG frame (esp_camera)\n-> HTTP POST -> show reply\non OLED (no OCR)", "A", ls="--", badge="PROPOSED")
    c.section(3.3, 3.0, 2.4, 2.15, "Wi-Fi (same LAN)", "C")
    c.box(3.4, 3.15, 2.2, 1.35, "POST /api/wearable/upload\nbody: image/jpeg\nreply: 3 lines of text", "C", badge="TESTED")
    c.section(6.1, 3.0, 2.8, 2.15, "Companion laptop (Python)", "B")
    c.box(6.25, 3.15, 2.5, 1.35, "Flask: store JPEG, validate,\nprocess_stored()\nexisting OCR/ML pipeline\n(unchanged)", "B", badge="TESTED")
    c.arrow((2.75, 3.95), (3.4, 3.95), "JPEG", ly=0.2, fs=6.4); c.arrow((5.6, 3.95), (6.25, 3.95), None)
    c.arrow((6.25, 3.4), (5.6, 3.4), None, color=PURPLE); c.arrow((3.4, 3.4), (2.75, 3.4), None, color=PURPLE)
    c.text(4.5, 3.18, "text reply", fs=6.2, color=PURPLE)
    c.section(0.1, 0.1, 8.8, 2.7, "Acquisition sources feeding the same pipeline (status of each)", "B")
    rows = [("1  Laptop webcam (OpenCV)", "IMPLEMENTED", "Capture + validation + pipeline. Tested with a test video file only; no physical webcam tested."),
            ("2  Image upload", "TESTED", "Automated tests with PNG/JPEG files; same entry point (identical results on identical pixels)."),
            ("3  Wearable camera (HTTP POST)", "NOT TESTED", "Receiver tested with a Python client. Firmware compiles and boots in Wokwi, camera init fails there (no camera part).\nNo physical camera, image capture or Wi-Fi POST from the device has been run.")]
    for i, (a, b, d) in enumerate(rows):
        y = 2.25 - i * 0.7
        c.text(0.3, y + 0.05, a, fs=7.0, ha="left", bold=True); c.badge(0.3, y - 0.35, b); c.text(3.2, y - 0.08, d, fs=6.2, ha="left", color="#333")
    c.save("comm_architecture")


def software_app_architecture():
    c = Canvas(9.0, 4.4)
    c.text(4.5, 4.2, "Companion application architecture (acquisition + recognition software)", fs=9.2, bold=True)
    c.box(0.15, 2.5, 1.9, 1.2, "Browser UI\nacquire.html\npreview, capture,\nupload, retake, process", "B", badge="TESTED")
    c.box(2.45, 2.5, 2.2, 1.2, "Flask server\nacquisition/server.py\n/api/cameras, /camera/*,\n/upload, /process, /wearable/*", "B", badge="TESTED")
    c.arrow((2.05, 3.1), (2.45, 3.1), None); c.arrow((2.45, 2.8), (2.05, 2.8), None)
    c.box(5.05, 3.0, 1.8, 0.7, "CameraManager\n(OpenCV, thread)", "B", fs=7); c.box(5.05, 2.1, 1.8, 0.7, "CaptureStore\n+ validate_frame", "B", fs=7)
    c.arrow((4.65, 3.35), (5.05, 3.35), None); c.arrow((4.65, 2.8), (5.05, 2.45), None)
    c.box(7.15, 2.5, 1.7, 1.2, "Webcam / USB cam\n(or test video file)\n\nuploaded file", "gray", fs=6.8); c.arrow((6.85, 3.35), (7.15, 3.35), None)
    c.box(2.45, 0.6, 2.2, 1.0, "analyse_image()\nexisting pipeline\n(unchanged)", "rej"); c.arrow((3.55, 2.5), (3.55, 1.6), "process_stored", lx=0.7, fs=6.4)
    c.box(5.05, 0.6, 1.8, 1.0, "models/*.joblib\ndeployment.json", "gray", fs=7); c.arrow((5.05, 1.1), (4.65, 1.1), None)
    c.box(0.15, 0.6, 1.9, 1.0, "Wearable camera\nPOST JPEG ->\n3-line text reply", "A", fs=6.8, badge="PROPOSED"); c.arrow((2.05, 1.1), (2.45, 1.1), None, ls="--", lw=1.0)
    c.text(4.5, 0.25, "The result (decision, text, readability, p, tau, guidance, timings) goes to the browser UI; the wearable gets a short text reply.", fs=6.4, color="#333")
    c.save("software_app_architecture")


if __name__ == "__main__":
    for f in (wrist_unit_layout, acquisition_workflow, companion_pipeline, ocr_ml_workflow, comm_architecture, software_app_architecture):
        f()
