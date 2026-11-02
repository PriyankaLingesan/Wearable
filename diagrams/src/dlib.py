"""Tiny drawing helpers shared by the project's matplotlib diagrams (consistent look, live SVG text)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

matplotlib.rcParams.update({"svg.fonttype": "none", "font.family": "DejaVu Sans", "pdf.fonttype": 42})
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PURPLE = "#6A1B9A"
COL = {"A": ("#FFF1D6", "#B7791F"), "B": ("#EAF1FB", "#2F5D8C"), "C": ("#E3F4E5", "#2E7D32"),
       "secA": ("#FFFBF2", "#B7791F"), "secB": ("#F6F9FE", "#2F5D8C"), "secC": ("#F4FBF5", "#2E7D32"),
       "rej": ("#FDE9E7", "#C62828"), "led": ("#FFFFFF", "#B7791F"), "gray": ("#F2F2F2", "#777777"), "sw": ("#EAF1FB", "#2F5D8C")}
BADGE = {"IMPLEMENTED": "#2E7D32", "TESTED": "#1B5E20", "PROPOSED": "#B7791F", "SIMULATED": "#2F5D8C", "NOT TESTED": "#C62828", "TEST ONLY": "#6D4C41"}


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.fig = plt.figure(figsize=(w, h)); self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, w); self.ax.set_ylim(0, h); self.ax.axis("off")

    def section(self, x, y, w, h, title, key, fs=8.6):
        fc, ec = COL["sec" + key]
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.1", fc=fc, ec=ec, lw=1.8))
        self.ax.text(x + 0.15, y + h - 0.2, title, fontsize=fs, fontweight="bold", color=ec, va="center")

    def box(self, x, y, w, h, text, key="B", n=None, fs=7.4, ls="-", lw=1.3, bold_first=True, badge=None):
        f, e = COL[key]
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.06", fc=f, ec=e, lw=lw, ls=ls))
        lines = text.split("\n"); lh = fs * 1.38 / 72; y0 = y + h / 2 + (len(lines) - 1) * lh / 2
        for i, t in enumerate(lines):
            self.ax.text(x + w / 2, y0 - i * lh, t, ha="center", va="center", fontsize=fs, fontweight="bold" if (i == 0 and bold_first) else "normal")
        if n is not None:
            self.ax.add_patch(plt.Circle((x + 0.03, y + h - 0.03), 0.14, fc="#222", ec="white", lw=0.8, zorder=5))
            self.ax.text(x + 0.03, y + h - 0.03, str(n), color="white", fontsize=7.2, fontweight="bold", ha="center", va="center", zorder=6)
        if badge:
            self.badge(x + w - 0.04, y + 0.04, badge, ha="right")

    def badge(self, x, y, label, ha="left", fs=5.8):
        c = BADGE[label]
        self.ax.text(x, y, " " + label + " ", fontsize=fs, color="white", fontweight="bold", ha=ha, va="bottom", zorder=9,
                     bbox=dict(boxstyle="round,pad=0.15", fc=c, ec="none"))

    def arrow(self, p, q, label=None, lx=0.0, ly=0.0, color="#333", lw=1.5, fs=7.0, ha="center", ls="-"):
        self.ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=12, lw=lw, color=color, shrinkA=0, shrinkB=0, zorder=4, ls=ls))
        if label:
            self.ax.text((p[0] + q[0]) / 2 + lx, (p[1] + q[1]) / 2 + ly, label, fontsize=fs, ha=ha, va="center", color=color,
                         bbox=dict(fc="white", ec="none", pad=0.8), zorder=7)

    def text(self, x, y, s, fs=7, color="#333", ha="center", bold=False, va="center"):
        self.ax.text(x, y, s, fontsize=fs, color=color, ha=ha, va=va, fontweight="bold" if bold else "normal")

    def save(self, name):
        for ext, kw in (("png", {"dpi": 300}), ("svg", {}), ("pdf", {})):
            self.fig.savefig(os.path.join(OUT, f"{name}.{ext}"), **kw)
        plt.close(self.fig); print("saved", name)
