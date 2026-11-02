"""Single-column architecture figure (paper Fig. 1). Run: python3 diagrams/src/architecture_integrated.py
Three image sources feed one Python pipeline. Wearable camera = PROPOSED, untested; webcam = implemented (test video only); upload = tested."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dlib import Canvas, PURPLE

c = Canvas(3.4, 3.7)
bw, bh, y0 = 1.05, 0.78, 2.85
xs0 = [0.05, 1.175, 2.3]
c.box(xs0[0], y0, bw, bh, "Wearable\ncamera unit\n(ESP32S3)", "A", fs=6.2, ls="--", badge="PROPOSED")
c.box(xs0[1], y0, bw, bh, "Laptop\nwebcam\n(OpenCV)", "B", fs=6.2, badge="IMPLEMENTED")
c.box(xs0[2], y0, bw, bh, "Image\nupload\n(file)", "B", fs=6.2, badge="TESTED")
c.section(0.05, 0.05, 3.3, 2.45, "Python companion (laptop), one pipeline", "B", fs=6.6)
w, h = 1.38, 0.78
c.box(0.15, 1.35, w, h, "Quality +\nlocalisation", "B", fs=6.2)
c.box(1.87, 1.35, w, h, "Two OCR engines\n(RapidOCR,\nTesseract)", "B", fs=6.2)
c.box(0.15, 0.2, w, h, "Result: accept /\nretake / no mark\n+ hint", "C", fs=6.2)
c.box(1.87, 0.2, w, h, "Calibrated\nrejection (ExtraTrees\n+ isotonic)", "rej", fs=6.2)
c.arrow((0.15 + w, 1.74), (1.87, 1.74))
c.arrow((1.87 + w / 2, 1.35), (1.87 + w / 2, 0.98))
c.arrow((1.87, 0.59), (0.15 + w, 0.59))
for x in xs0: c.arrow((x + bw / 2, y0), (x + bw / 2, 2.5), None, color=PURPLE if x == xs0[0] else "#333")
c.text(0.66, 2.67, "HTTP POST (JPEG)", fs=5.6, color=PURPLE, ha="left")
c.text(1.7, 1.18, "Readability (Random Forest) alongside", fs=5.6, color="#2F5D8C")
c.save("architecture_integrated")
