"""Camera and optical sensing schematic (side view + signal path). DESIGN ESTIMATE ONLY: not built, not simulated (Wokwi has no camera).
Numbers: OV2640 (Arducam datasheet page): 1600x1200, EFL 4.22 mm, 52 deg diagonal FOV, fixed focus (macro focus range NOT specified; must be verified).
FOV width = 2 d tan(26 deg) * 0.8 = 0.78 d (4:3 sensor).  Run: python3 diagrams/src/camera_sensing_schematic.py"""
import os, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyBboxPatch, FancyArrowPatch, Circle
matplotlib.rcParams.update({"svg.fonttype": "none", "font.family": "DejaVu Sans", "pdf.fonttype": 42})
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
fig = plt.figure(figsize=(13, 7.4)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 13); ax.set_ylim(0, 7.4); ax.axis("off")
d = 30.0; fovw = 0.78 * d; ppmm = 1600 / fovw
sc = 0.115  # inches per mm in the side view
x0 = 4.2; ysurf = 1.2
# jewellery surface + hallmark
ax.add_patch(Rectangle((x0 - 2.1, ysurf - 0.35), 4.2, 0.35, fc="#E8C766", ec="#8a6a10", lw=1.5))
ax.add_patch(Rectangle((x0 - 0.5, ysurf - 0.05), 1.0, 0.05, fc="#6b4e0a", ec="none"))
ax.text(x0, ysurf - 0.62, "Gold jewellery surface with engraved / stamped / laser-marked hallmark", ha="center", fontsize=9)
# camera module
ycam = ysurf + d * sc
ax.add_patch(FancyBboxPatch((x0 - 0.7, ycam), 1.4, 0.75, boxstyle="round,pad=0,rounding_size=0.05", fc="#FFF1D6", ec="#B7791F", lw=1.6))
ax.text(x0, ycam + 0.52, "Camera module", ha="center", fontsize=9, fontweight="bold")
ax.text(x0, ycam + 0.24, "OV2640 optics assumed\n(placeholder)", ha="center", fontsize=8)
ax.add_patch(Polygon([[x0 - 0.18, ycam], [x0 + 0.18, ycam], [x0 + 0.18, ycam - 0.12], [x0 - 0.18, ycam - 0.12]], fc="#9ecae1", ec="#2F5D8C"))
# FOV cone
half = fovw / 2 * sc
ax.add_patch(Polygon([[x0, ycam - 0.12], [x0 - half, ysurf], [x0 + half, ysurf]], fc="#2F5D8C", alpha=0.12, ec="#2F5D8C", lw=1.0, ls="--"))
ax.annotate("", xy=(x0 - half, ysurf + 0.15), xytext=(x0 + half, ysurf + 0.15), arrowprops=dict(arrowstyle="<->", color="#2F5D8C"))
ax.text(x0, ysurf + 0.32, f"FOV width ≈ {fovw:.0f} mm  (≈ {ppmm:.0f} px/mm on 1600 px)", ha="center", fontsize=8.5, color="#2F5D8C")
ax.annotate("", xy=(x0 + 1.5, ycam - 0.12), xytext=(x0 + 1.5, ysurf), arrowprops=dict(arrowstyle="<->", color="#333"))
ax.text(x0 + 1.6, (ycam + ysurf) / 2, "working distance d ≈ 30 mm\n(design target; the lens must\nbe refocused for this range)", fontsize=8.5, va="center")
# LED ring (illumination) at ~off-axis angle
for sgn in (-1, 1):
    lx = x0 + sgn * 1.25; ly = ycam - 0.65
    ax.add_patch(Circle((lx, ly), 0.13, fc="white", ec="#B7791F", lw=2))
    ax.add_patch(FancyArrowPatch((lx, ly - 0.14), (x0 + sgn * 0.3, ysurf + 0.02), arrowstyle="-|>", mutation_scale=12, color="#E0A000", lw=1.6))
ax.text(x0 - 3.0, ycam - 0.55, "White LED illumination\n(2 x LED, oblique, ~30–40° from axis;\nnot a sensor; GPIO1/D0 via driver)", ha="center", fontsize=8.5, color="#8a6a10")
ax.text(9.6, 2.6, "Glare control: oblique, diffuse light;\nrecapture hint “glare” if saturated\nregion on the mark", ha="center", fontsize=8.2, color="#8a6a10")
# signal path to ESP32
ax.add_patch(FancyBboxPatch((7.9, ycam - 0.1), 2.0, 0.95, boxstyle="round,pad=0,rounding_size=0.05", fc="#FFF1D6", ec="#B7791F", lw=1.6))
ax.text(8.9, ycam + 0.55, "XIAO ESP32S3 Sense", ha="center", fontsize=8.6, fontweight="bold"); ax.text(8.9, ycam + 0.22, "DVP camera interface,\nJPEG encode, Wi-Fi", ha="center", fontsize=8)
ax.add_patch(FancyArrowPatch((x0 + 0.7, ycam + 0.38), (7.9, ycam + 0.38), arrowstyle="-|>", mutation_scale=14, color="#333", lw=1.8))
ax.text(6.35, ycam + 0.58, "DVP (B2B)", ha="center", fontsize=8)
ax.add_patch(FancyBboxPatch((10.6, ycam - 0.1), 2.1, 0.95, boxstyle="round,pad=0,rounding_size=0.05", fc="#EAF1FB", ec="#2F5D8C", lw=1.6))
ax.text(11.65, ycam + 0.55, "Companion (Python)", ha="center", fontsize=9.5, fontweight="bold"); ax.text(11.65, ycam + 0.22, "quality > localise > OCR\n> rejection > guidance", ha="center", fontsize=8)
ax.add_patch(FancyArrowPatch((9.9, ycam + 0.38), (10.6, ycam + 0.38), arrowstyle="-|>", mutation_scale=14, color="#6A1B9A", lw=2.2))
ax.text(10.25, ycam + 0.62, "HTTP", ha="center", fontsize=8, color="#6A1B9A")
# notes
ax.text(0.3, 7.2, "Camera and optical sensing schematic (PROPOSED design, not built, not simulated)", fontsize=12.5, fontweight="bold")
notes = ("Status: design estimate only. Wokwi cannot simulate a camera, so experiments use synthetic images in place of this sensor.\n"
         "Proposed module: OV5640 AF (the vendor says kits may ship with an OV5640 or OV3660, so the fitted module is unconfirmed); no field of view or minimum focus distance is listed, so they cannot be\n"
         "estimated here. The cone and the 23 mm figure below use OV2640 numbers (Arducam page: 1600x1200, fixed focus, EFL 4.22 mm, 52 deg diagonal FOV) as an illustrative PLACEHOLDER, not OV5640 values,\n"
         "and all optical values are estimates; macro focus must be measured on the delivered module (refocus, or add a close-up lens) before any build.\n"
         "Fallback architecture: USB macro camera on the companion computer (no image transfer from the wrist unit).")
ax.text(0.3, 6.45, notes, fontsize=8.6, va="top", color="#333")
# estimated characters
ax.text(0.3, 0.35, f"Example: a 1.5 mm character is ≈ {1.5*ppmm:.0f} px tall at d = 30 mm; the synthetic images used in the experiments are 640x400 px, i.e. a lower resolution than this design.", fontsize=8.6, color="#333")
for ext, kw in (("png", {"dpi": 250}), ("svg", {}), ("pdf", {})):
    fig.savefig(os.path.join(OUT, f"camera_sensing_schematic.{ext}"), **kw)
print(fovw, ppmm)
