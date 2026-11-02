"""Circuit of the Wokwi project hardware/wokwi_xiao_s3/diagram.json, drawn as a schematic with its components.
NOT a Wokwi screenshot (the Wokwi site could not be opened when this was made). Wokwi has no camera part, so the camera is shown only as a note.
Run: python3 diagrams/src/wokwi_circuit.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon
from dlib import OUT

W, H = 6.8, 4.5
fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
sx, sy = 0.78, 0.86
X = lambda x: x * sx
Y = lambda y: y * sy
FS = 6.4
def line(pts, color="#222", lw=1.1, ls="-"):
    ax.plot([X(p[0]) for p in pts], [Y(p[1]) for p in pts], color=color, lw=lw, ls=ls, solid_capstyle="round", zorder=3)
def txt(x, y, s, fs=FS, ha="center", color="#222", bold=False, va="center"):
    ax.text(X(x), Y(y), s, fontsize=fs, ha=ha, va=va, color=color, fontweight="bold" if bold else "normal", zorder=6)
def dot(x, y): ax.plot([X(x)], [Y(y)], "o", color="#222", ms=2.6, zorder=5)
def gnd(x, y):
    line([(x, y), (x, y - 0.12)]); 
    for i, w in enumerate((0.16, 0.10, 0.04)): line([(x - w, y - 0.12 - i * 0.05), (x + w, y - 0.12 - i * 0.05)], lw=1.0)

# ---- board ----
bx0, bx1, by0, by1 = 3.2, 4.8, 0.55, 4.35
ax.add_patch(FancyBboxPatch((X(bx0), Y(by0)), X(bx1) - X(bx0), Y(by1) - Y(by0), boxstyle="round,pad=0,rounding_size=0.08", fc="#1f6f43", ec="#0e3b24", lw=1.6, zorder=2))
ax.add_patch(Rectangle((X(3.7), Y(by1) - 0.12), X(0.6), 0.2, fc="#c8c8c8", ec="#777", zorder=3)); txt(4.0, 4.55, "USB-C", fs=5.4)
txt(4.0, 4.2, "XIAO ESP32-S3", bold=True, color="white", fs=7); txt(4.0, 4.05, "(Sense board)", color="white", fs=5.8)
lp = ["D0", "D1", "D2", "D3", "D4", "D5", "D6"]; rp = ["5V", "GND", "3V3", "D10", "D9", "D8", "D7"]
ys = [3.75 - i * 0.40 for i in range(7)]
for i, y in enumerate(ys):
    txt(bx0 + 0.12, y, lp[i], fs=5.8, ha="left", color="white"); txt(bx1 - 0.12, y, rp[i], fs=5.8, ha="right", color="white")
    for xx in (bx0, bx1): ax.plot([X(xx)], [Y(y)], "s", color="#e8c25a", ms=3.2, zorder=4)
ax.add_patch(Rectangle((X(3.4), Y(0.7)), X(1.2), Y(0.5) - Y(0.0), fc="#17543a", ec="white", ls="--", lw=0.9, zorder=3))
txt(4.0, 0.95, "camera connector", fs=5.4, color="white"); txt(4.0, 0.78, "no Wokwi part, not simulated", fs=5.4, color="#ffd7d7")
yD = dict(zip(lp, ys)); yR = dict(zip(rp, ys))

# ---- D0 -> 220 ohm -> white LED -> GND (left) ----
y = yD["D0"]
line([(bx0, y), (2.6, y)]); 
ax.add_patch(Rectangle((X(1.85), Y(y) - 0.09), X(0.75), 0.18, fc="#e9d6b0", ec="#6b4e0a", zorder=4)); txt(2.22, y + 0.26, "R 220 Ω", fs=6)
line([(1.85, y), (1.35, y)])
ax.add_patch(Polygon([[X(1.35), Y(y) + 0.13], [X(1.35), Y(y) - 0.13], [X(0.95), Y(y)]], fc="white", ec="#222", lw=1.1, zorder=4)); line([(0.95, y + 0.13), (0.95, y - 0.13)], lw=1.3)
txt(1.15, y + 0.34, "white LED\n(ILLUM)", fs=6)
line([(0.95, y), (0.55, y), (0.55, y - 0.2)]); gnd(0.55, y - 0.2)


# ---- D1 -> CAPTURE button -> GND (left) ----
y = yD["D1"]
line([(bx0, y), (2.5, y)]); dot(2.5, y); 
line([(2.5, y), (1.9, y + 0.16)], lw=1.3); dot(1.8, y); line([(1.8, y), (1.3, y), (1.3, y - 0.2)]); gnd(1.3, y - 0.2)
txt(2.0, y - 0.42, "CAPTURE button\n(internal pull-up)", fs=6)

# ---- OLED (right) ----
ox0, ox1, oy0, oy1 = 6.5, 8.6, 2.2, 4.1
ax.add_patch(FancyBboxPatch((X(ox0), Y(oy0)), X(ox1) - X(ox0), Y(oy1) - Y(oy0), boxstyle="round,pad=0,rounding_size=0.05", fc="#222", ec="#000", lw=1.2, zorder=2))
ax.add_patch(Rectangle((X(7.05), Y(2.55)), X(1.35), Y(3.65) - Y(2.55), fc="#0b0b0b", ec="#555", zorder=3)); txt(7.72, 3.1, "128x64", fs=7, color="#f5c542")
txt(7.55, 4.3, "SSD1306 OLED module (I²C 0x3C)", fs=6)
op = {"VCC": 3.8, "GND": 3.5, "SDA": 3.2, "SCL": 2.9}
for n, yy in op.items():
    ax.plot([X(ox0)], [Y(yy)], "s", color="#e8c25a", ms=3.2, zorder=5); txt(ox0 + 0.1, yy, n, fs=5.6, ha="left", color="white")
# 3V3 -> VCC
y3 = yR["3V3"]; line([(bx1, y3), (5.3, y3), (5.3, op["VCC"]), (ox0, op["VCC"])], color="#c62828"); txt(5.55, op["VCC"] + 0.14, "3V3", fs=5.6, color="#c62828")
# GND stubs
line([(bx1, yR["GND"]), (5.05, yR["GND"])]); gnd(5.05, yR["GND"])
line([(ox0, op["GND"]), (6.25, op["GND"])]); gnd(6.25, op["GND"])
# D4 -> SDA, D5 -> SCL around the bottom of the board
yd4, yd5 = yD["D4"], yD["D5"]
line([(bx0, yd4), (3.0, yd4), (3.0, 0.38), (5.7, 0.38), (5.7, op["SDA"]), (ox0, op["SDA"])], color="#2e7d32")
line([(bx0, yd5), (2.85, yd5), (2.85, 0.22), (5.95, 0.22), (5.95, op["SCL"]), (ox0, op["SCL"])], color="#1565c0")
txt(4.4, 0.47, "D4 = SDA", fs=5.8, color="#2e7d32"); txt(4.4, 0.13, "D5 = SCL", fs=5.8, color="#1565c0")

txt(W / sx / 2, 5.15, "Wokwi project circuit (hardware/wokwi_xiao_s3/diagram.json): XIAO ESP32-S3, OLED, button, resistor, LED", fs=7.4, bold=True)
txt(W / sx / 2, 4.93, "Redrawn from diagram.json, not a Wokwi screenshot. Simplified: resistor-driven LED (the proposed unit uses a transistor stage). Wokwi has no camera part.", fs=5.8, color="#8a5a00")
for ext, kw in (("png", {"dpi": 300}), ("svg", {}), ("pdf", {})):
    fig.savefig(os.path.join(OUT, f"wokwi_circuit.{ext}"), **kw)
print("saved")
