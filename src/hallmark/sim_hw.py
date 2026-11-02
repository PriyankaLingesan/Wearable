"""SIMULATED wearable hardware: OLED frame renderer and camera/LED model.

Nothing here talks to real hardware. The OLED bitmap is a real 128x64 1-bit frame (as an SSD1306-class
module would receive); the camera is the synthetic
acquisition generator from `synth.py`."""
import io
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
W, H = 128, 64

def _f(size, bold=True):
    return ImageFont.truetype(FONT if bold else FONT_B, size)


def render_oled(decision, text, p_correct, readability, guidance, risk_target):
    """Return a 128x64 PIL image in mode '1'."""
    img = Image.new("1", (W, H), 0)
    d = ImageDraw.Draw(img)
    if decision == "accept":
        d.text((0, 0), "READ OK", font=_f(10), fill=1)
        d.text((74, 1), f"p={p_correct:.2f}", font=_f(9, False), fill=1)
        size = 16 if len(text) <= 9 else (12 if len(text) <= 13 else 9)
        d.text((0, 16), text[:20], font=_f(size), fill=1)
        d.line((0, 40, 127, 40), fill=1)
        d.text((0, 43), f"{readability}", font=_f(9, False), fill=1)
        d.text((0, 54), f"risk<={int(risk_target*100)}% mode", font=_f(8, False), fill=1)
    elif decision == "no_mark":
        d.text((0, 0), "NO MARK", font=_f(12), fill=1)
        d.text((0, 22), "Aim at inscription", font=_f(9, False), fill=1)
        d.text((0, 34), "and press A", font=_f(9, False), fill=1)
    else:
        d.rectangle((0, 0, 127, 11), fill=1)
        d.text((2, 0), "RETAKE", font=_f(10), fill=0)
        d.text((78, 1), f"p={p_correct:.2f}", font=_f(9, False), fill=0)
        for i, line in enumerate(textwrap.wrap(guidance, 21)[:3]):
            d.text((0, 15 + 11 * i), line, font=_f(9, False), fill=1)
        d.text((0, 54), f"{readability}", font=_f(8, False), fill=1)
    return img


def oled_png(img, scale=5):
    big = img.resize((W * scale, H * scale), Image.NEAREST).convert("L")
    buf = io.BytesIO(); big.save(buf, "PNG")
    return buf.getvalue()


def led_effect(params, led_on):
    """Simulated LED ring: reduces illumination non-uniformity and slightly lifts brightness. A model, not a measurement."""
    p = dict(params)
    if led_on:
        p["illum"] = p.get("illum", 0.0) * 0.5
    return p
