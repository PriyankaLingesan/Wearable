"""Editable source for the main system-architecture diagram (Fig. 1 of the paper, slide 8).
Run:  python3 diagrams/src/architecture_main.py   ->  diagrams/architecture_main.{svg,png,pdf}
All block positions are plain numbers below (inches); text stays live in the SVG (svg.fonttype=none), so the SVG
can also be edited in Inkscape / PowerPoint. The diagram shows the implemented pipeline (src/hallmark/pipeline.py,
models.py, sim_hw.py); nothing here is un-implemented. Camera/LED/OLED are SIMULATED in software."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Circle, Rectangle

matplotlib.rcParams.update({"svg.fonttype": "none", "font.family": "DejaVu Sans", "pdf.fonttype": 42})
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, H = 7.9, 4.25
fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

C_PROC, E_PROC = "#EAF1FB", "#2F5D8C"      # implemented processing blocks
C_SIM, E_SIM = "#FFF1D6", "#B7791F"        # simulated hardware
C_ACC, E_ACC = "#E3F4E5", "#2E7D32"
C_REJ, E_REJ = "#FDE9E7", "#C62828"
FS = 6.4

def box(x, y, w, h, text, fc=C_PROC, ec=E_PROC, fs=FS, bold_first=True, lw=1.0, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.05", fc=fc, ec=ec, lw=lw, ls=ls))
    lines = text.split("\n")
    n = len(lines); lh = fs * 1.35 / 72
    y0 = y + h / 2 + (n - 1) * lh / 2
    for i, t in enumerate(lines):
        ax.text(x + w / 2, y0 - i * lh, t, ha="center", va="center", fontsize=fs, fontweight="bold" if (i == 0 and bold_first) else "normal")

def arrow(p, q, label=None, lpos=(0, 0.07), color="#444444", head=True, fs=5.8, ha="center"):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>" if head else "-", color=color, lw=0.9, shrinkA=0, shrinkB=0, mutation_scale=7))
    if label:
        ax.text((p[0] + q[0]) / 2 + lpos[0], (p[1] + q[1]) / 2 + lpos[1], label, fontsize=fs, color=color, ha=ha, va="center")

def line(pts, color="#444444"):
    xs, ys = zip(*pts); ax.plot(xs, ys, color=color, lw=0.9, solid_capstyle="butt")

def badge(x, y, n):
    ax.add_patch(Circle((x, y), 0.085, fc="#1F3A5F", ec="none")); ax.text(x, y, str(n), color="white", fontsize=5.8, ha="center", va="center", fontweight="bold")

# ---- lanes ----
yM = 1.98
# 1 capture (simulated)
box(0.05, 1.63, 0.78, 0.70, "Simulated\ncamera + LED\n640x400 frame", C_SIM, E_SIM); badge(0.13, 2.33, 1)
# 2 localise
box(0.98, 1.63, 0.80, 0.70, "Localisation\n(gradient-energy\ncontour) -> ROI", fs=FS - 0.2); badge(0.98, 2.33, 2)
arrow((0.83, yM), (0.98, yM))
# image-quality features (top lane)
box(1.22, 3.18, 1.78, 0.62, "Image-quality features (21)\nsharpness, contrast, illumination,\nglare, noise, ROI size", fs=FS - 0.3); badge(1.22, 3.80, "Q")
line([(0.44, 2.33), (0.44, 3.49)]); arrow((0.44, 3.49), (1.22, 3.49), label="frame", lpos=(0, 0.1))
arrow((1.38, 2.33), (1.38, 3.18), label="ROI", lpos=(0.17, 0), ha="left")
# 3 parallel OCR
ax.add_patch(Rectangle((1.95, 1.03), 1.08, 2.02, fc="none", ec="#7A7A7A", lw=0.9, ls=(0, (4, 2))))
ax.text(2.49, 2.93, "PARALLEL OCR", fontsize=5.4, ha="center", va="center", color="#555555", fontweight="bold")
box(2.02, 2.10, 0.94, 0.62, "OCR-A\nRapidOCR\nraw gray ROI", fs=FS - 0.3); box(2.02, 1.18, 0.94, 0.62, "OCR-B\nTesseract LSTM\nred-channel ROI", fs=FS - 0.3); badge(1.95, 3.05, 3)
line([(1.78, yM), (1.87, yM)]); line([(1.87, 1.49), (1.87, 2.41)]); arrow((1.87, 2.41), (2.02, 2.41)); arrow((1.87, 1.49), (2.02, 1.49))
# 4 uncertainty features
box(3.17, 1.18, 0.90, 1.54, "OCR-uncertainty\nfeatures\nconfidences, A/B\ndisagreement,\nstring length", fs=FS - 0.3); badge(3.17, 2.72, 4)
arrow((2.96, 2.41), (3.17, 2.41)); arrow((2.96, 1.49), (3.17, 1.49))
# 5 calibrated rejector
box(4.25, 1.52, 0.90, 0.92, "Calibrated\nrejector\nExtraTrees +\nisotonic\np = P(correct)", fs=FS - 0.4); badge(4.25, 2.44, 5)
arrow((4.07, yM), (4.25, yM))
# quality bus -> rejector (down) and readability classifier (east)
line([(3.00, 3.49), (4.60, 3.49)]); arrow((4.60, 3.49), (4.60, 2.44)); ax.add_patch(Circle((4.60, 3.49), 0.03, fc="#444444", ec="none"))
box(4.95, 3.18, 1.00, 0.62, "Readability\nclassifier\nRandomForest", fs=FS - 0.3); arrow((4.60, 3.49), (4.95, 3.49))
ax.text(3.8, 3.60, "quality features", fontsize=5.6, color="#444444", ha="center")
# 6 decision
ax.add_patch(Polygon([(5.62, 2.38), (5.94, 1.98), (5.62, 1.58), (5.30, 1.98)], fc="#FFF8DC", ec="#B7791F", lw=1.0))
ax.text(5.62, 1.98, "p >= tau ?", fontsize=5.8, ha="center", va="center", fontweight="bold"); badge(5.30, 2.38, 6)
arrow((5.15, yM), (5.30, yM), label="p", lpos=(0, 0.08))
# 7 simulated wearable output (container)
ax.add_patch(FancyBboxPatch((6.44, 0.06), 1.42, 4.10, boxstyle="round,pad=0,rounding_size=0.06", fc="#FFFBF2", ec=E_SIM, lw=1.1, ls=(0, (4, 2))))
ax.text(7.15, 3.98, "SIMULATED WEARABLE OUTPUT", fontsize=5.4, ha="center", va="center", color=E_SIM, fontweight="bold"); badge(6.44, 4.16, 7)
box(6.54, 3.18, 1.22, 0.62, "OLED 128x64\nreadability label\n(readable / partial / unreadable)", C_SIM, E_SIM, fs=5.4)
box(6.54, 1.60, 1.22, 0.78, "ACCEPT\nOLED: transcription", C_ACC, E_ACC, fs=FS - 0.3)
box(6.54, 0.18, 1.22, 0.78, "RETAKE\nOLED: hint", C_REJ, E_REJ, fs=FS - 0.3)
arrow((5.95, 3.49), (6.54, 3.49))
arrow((5.94, yM), (6.54, yM), label="Accept", lpos=(0, 0.1), color=E_ACC)
# reject -> guidance -> retake
arrow((5.62, 1.58), (5.62, 0.85), label="Reject", lpos=(0.26, 0), color=E_REJ)
box(4.95, 0.25, 1.00, 0.60, "Recapture\nguidance\nlargest deficit -> hint", fs=FS - 0.4)
arrow((5.95, 0.55), (6.54, 0.55))
# quality connector into guidance
ax.add_patch(Circle((3.40, 0.55), 0.085, fc="white", ec="#444444", lw=0.9)); ax.text(3.40, 0.55, "Q", fontsize=5.8, ha="center", va="center", fontweight="bold")
arrow((3.485, 0.55), (4.95, 0.55), label="quality deficits (from Q)", lpos=(0, 0.1))
# legend
ax.add_patch(Rectangle((0.05, 0.06), 2.85, 0.92, fc="white", ec="#BBBBBB", lw=0.6))
ax.add_patch(FancyBboxPatch((0.12, 0.74), 0.20, 0.12, boxstyle="round,pad=0,rounding_size=0.02", fc=C_PROC, ec=E_PROC, lw=0.8)); ax.text(0.40, 0.80, "implemented processing block", fontsize=5.4, va="center")
ax.add_patch(FancyBboxPatch((0.12, 0.54), 0.20, 0.12, boxstyle="round,pad=0,rounding_size=0.02", fc=C_SIM, ec=E_SIM, lw=0.8)); ax.text(0.40, 0.60, "simulated hardware (software model)", fontsize=5.4, va="center")
ax.add_patch(Rectangle((0.12, 0.34), 0.20, 0.12, fc="none", ec="#7A7A7A", lw=0.8, ls=(0, (4, 2)))); ax.text(0.40, 0.40, "parallel branch / grouped output", fontsize=5.4, va="center")
ax.text(0.12, 0.17, "1-7: processing order;  Q: quality features reused;  tau: risk-target threshold", fontsize=5.0, va="center", color="#444444")
for ext in ("svg", "png", "pdf"):
    fig.savefig(os.path.join(OUT, f"architecture_main.{ext}"), dpi=450 if ext == "png" else None)
print("ok")
