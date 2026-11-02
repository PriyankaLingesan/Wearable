"""Synthetic engraved-hallmark image generator.

EVERYTHING produced here is SYNTHETIC. Images are procedural renderings of fictitious inscriptions
on a procedural metal-like texture. They are NOT photographs of real jewellery and the inscriptions
are NOT real hallmark registrations (the 6-character codes are random). Readability labels are a
generator-defined proxy computed from measured legibility factors, not human judgements.
"""
import json
import random
import string

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.morphology import skeletonize

F = "/usr/share/fonts/truetype/"
SOURCES = {
    # Three rendering families. They emulate "different acquisition domains" only in a loose,
    # synthetic sense (different fonts, metal tint, light direction, texture statistics).
    "S1": dict(fonts=[F + "dejavu/DejaVuSansMono-Bold.ttf", F + "dejavu/DejaVuSans-Bold.ttf"],
               base=(62, 160, 212), light=(-0.7, -0.7), grain=0.05, brush=0.07, relief=0.60),
    "S2": dict(fonts=[F + "freefont/FreeSansBold.ttf", F + "crosextra/Carlito-Bold.ttf",
                      F + "dejavu/DejaVuSerif-Bold.ttf"],
               base=(110, 150, 200), light=(0.7, -0.7), grain=0.07, brush=0.10, relief=0.50),
    "S3": dict(fonts=[F + "freefont/FreeMonoBold.ttf", F + "dejavu/DejaVuSansCondensed-Bold.ttf",
                      F + "crosextra/Caladea-Bold.ttf"],
               base=(150, 172, 190), light=(-0.3, 0.9), grain=0.09, brush=0.12, relief=0.45),
}
STYLES = ["engraved", "embossed", "stamped", "laser"]
PURITY = ["375", "585", "750", "916", "958", "999"]
KARAT = ["9K", "14K", "18K", "22K", "24K"]
MAKER_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"
CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ123456789"  # no I/O/0: avoids visually impossible ambiguity

CONDITIONS = ["clean", "blur", "lowres", "uneven_light", "glare", "lowcontrast", "angle",
              "occlusion", "noise", "combined", "severe"]


def make_text(rng):
    """Fictitious inscription following a documented grammar (see data/DATASHEET.md)."""
    toks = []
    r = rng.random()
    if r < 0.70:
        toks.append(rng.choice(PURITY))
    if rng.random() < 0.55:
        toks.append(rng.choice(KARAT))
    if rng.random() < 0.30:
        toks.append("BIS")
    if rng.random() < 0.45:
        toks.append("".join(rng.choice(CODE_CHARS) for _ in range(6)))
    if rng.random() < 0.35:
        toks.append("".join(rng.choice(MAKER_LETTERS) for _ in range(rng.choice([2, 3]))))
    if not toks:
        toks = [rng.choice(PURITY)]
    rng.shuffle(toks)
    text = " ".join(toks)
    if len(text.replace(" ", "")) < 4:
        text += " " + rng.choice(KARAT)
    return text[:16].strip()


def _metal_texture(shape, src, rng_np):
    h, w = shape
    base = np.array(src["base"], np.float32)[None, None, :]
    n = rng_np.normal(0, 1, (h, w)).astype(np.float32)
    k = np.zeros((1, 21), np.float32); k[0, :] = 1.0 / 21
    brushed = cv2.filter2D(n, -1, k)
    brushed = cv2.GaussianBlur(brushed, (0, 0), 0.8)
    brushed /= (brushed.std() + 1e-6)
    low = cv2.GaussianBlur(rng_np.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 70)
    low /= (low.std() + 1e-6)
    grain = rng_np.normal(0, 1, (h, w)).astype(np.float32)
    lum = 1.0 + src["brush"] * brushed + 0.06 * low + src["grain"] * grain
    return np.clip(base * lum[..., None], 0, 255)


def _render_mask(text, font_path, cap_h, size, rng):
    W, H = size
    # choose font size so that rendered cap height ~ cap_h
    fs = int(cap_h * 1.38)
    font = ImageFont.truetype(font_path, fs)
    img = Image.new("L", (W * 2, H * 2), 0)
    d = ImageDraw.Draw(img)
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    if tw > W * 0.88:  # shrink to fit
        fs = int(fs * (W * 0.88) / tw)
        font = ImageFont.truetype(font_path, fs)
        bb = d.textbbox((0, 0), text, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
    cx = W // 2 + rng.randint(-int(W * 0.04), int(W * 0.04))
    cy = H // 2 + rng.randint(-int(H * 0.06), int(H * 0.06))
    d.text((W - tw // 2 + (cx - W // 2) * 0 - bb[0], H - th // 2 - bb[1]), text, font=font, fill=255)
    m = np.array(img)
    # centre crop to canvas, then translate to (cx, cy)
    m = m[H // 2: H // 2 + H, W // 2: W // 2 + W]
    M = np.float32([[1, 0, cx - W // 2], [0, 1, cy - H // 2]])
    m = cv2.warpAffine(m, M, (W, H))
    ang = rng.uniform(-3, 3)
    R = cv2.getRotationMatrix2D((cx, cy), ang, 1.0)
    m = cv2.warpAffine(m, R, (W, H))
    return (m.astype(np.float32) / 255.0), font_path.split("/")[-1], fs


def _shade(base, mask, style, light, relief, rng_np, rng):
    mk = cv2.GaussianBlur(mask, (0, 0), 1.1)
    bev = rng.uniform(1.8, 3.2)
    depth = cv2.GaussianBlur(mask, (0, 0), bev)
    gx = cv2.Sobel(depth, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(depth, cv2.CV_32F, 0, 1, ksize=3)
    sign = -1.0 if style in ("engraved", "stamped") else 1.0
    sh = sign * (gx * light[0] + gy * light[1])
    sh /= (np.abs(sh).max() + 1e-6)
    out = base.copy()
    gain = {"engraved": 0.60, "embossed": 0.55, "stamped": 0.85, "laser": 0.22}[style] * (relief / 0.5)
    out *= (1.0 + gain * sh)[..., None]
    if style == "engraved":
        out *= (1 - 0.38 * mk)[..., None]
    elif style == "stamped":
        out *= (1 - 0.50 * mk)[..., None]
    elif style == "laser":
        out *= (1 - 0.58 * mk)[..., None] * np.array([0.95, 0.97, 1.0])[None, None, :]
    else:
        out *= (1 + 0.04 * mk)[..., None]
    spec = np.clip(sh, 0, None) ** 2 * 60.0
    out += spec[..., None]
    return np.clip(out, 0, 255)


def _homography(W, H, theta_deg, inplane_deg):
    th = np.deg2rad(theta_deg)
    c = np.cos(th)
    src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    # out-of-plane rotation about vertical axis: right side farther -> shrinks vertically and horizontally
    k = (1 - c) * 0.5
    dst = np.float32([[W * 0.05, H * 0.0 + H * k * 0.6],
                      [W * (1 - 0.05 * (1 - c) * 2) - W * k * 0.6, H * k * 0.9 + H * 0.05 * (1 - c)],
                      [W * (1 - 0.05 * (1 - c) * 2) - W * k * 0.6, H - H * k * 0.9 - H * 0.05 * (1 - c)],
                      [W * 0.05, H - H * k * 0.6]])
    dst = (dst - [W / 2, H / 2])
    a = np.deg2rad(inplane_deg)
    Rm = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]], np.float32)
    dst = dst @ Rm.T + [W / 2, H / 2]
    # keep full field of view roughly: scale to fill
    return cv2.getPerspectiveTransform(src, dst.astype(np.float32))


def _glare_field(shape, n, strength, rng, rng_np, near=None):
    h, w = shape
    f = np.zeros((h, w), np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    for _ in range(n):
        if near is not None and rng.random() < 0.8:
            cx = near[0] + rng.uniform(-0.25, 0.25) * w
            cy = near[1] + rng.uniform(-0.25, 0.25) * h
        else:
            cx, cy = rng.uniform(0, w), rng.uniform(0, h)
        sx, sy = rng.uniform(0.06, 0.22) * w, rng.uniform(0.05, 0.25) * h
        ang = rng.uniform(0, np.pi)
        dx, dy = xx - cx, yy - cy
        u = dx * np.cos(ang) + dy * np.sin(ang)
        v = -dx * np.sin(ang) + dy * np.cos(ang)
        f += np.exp(-0.5 * ((u / sx) ** 2 + (v / sy) ** 2))
    f = np.clip(f * strength, 0, 1.6)
    return f


def _ink_contrast(gray, mask_t):
    ink = mask_t > 0.5
    if ink.sum() < 20:
        return 0.0
    ring = cv2.dilate(ink.astype(np.uint8), np.ones((15, 15), np.uint8)) - cv2.dilate(
        ink.astype(np.uint8), np.ones((5, 5), np.uint8))
    ring = ring > 0
    if ring.sum() < 20:
        return 0.0
    mi, mr = gray[ink].mean(), gray[ring].mean()
    return float(abs(mi - mr) / max(mr, 1.0))


def _stroke_width(mask):
    sk = skeletonize(mask > 0.5)
    n = sk.sum()
    return float((mask > 0.5).sum() / max(n, 1))


def render_clean(spec, size=(640, 400)):
    """Render the pristine (undegraded) synthetic item described by `spec`."""
    W, H = size
    src = SOURCES[spec["source"]]
    rng = random.Random(spec["seed"])
    rng_np = np.random.default_rng(spec["seed"])
    base = _metal_texture((H, W), src, rng_np)
    mask, font_name, fs = _render_mask(spec["text"], spec["font_path"], spec["cap_h"], size, rng)
    img = _shade(base, mask, spec["style"], src["light"], src["relief"], rng_np, rng)
    return img.astype(np.float32), mask


def sample_degradation(cond, rng, level=None):
    """Sample degradation parameters for acquisition type `cond`."""
    p = dict(blur_sigma=0.0, motion_len=0, scale=1.0, illum=0.0, glare_n=0, glare_s=0.0,
             contrast=1.0, theta=0.0, inplane=rng.uniform(-3, 3), occ=0.0, noise=0.0, jpeg=95)

    def add(kind, lvl):
        if level is not None:  # explicit severity override (used by the simulator's severity slider)
            lvl = float(level)
        if kind == "blur":
            if rng.random() < 0.7:
                p["blur_sigma"] = max(p["blur_sigma"], rng.uniform(0.8, 1.0 + 12.0 * lvl))
            else:
                p["motion_len"] = max(p["motion_len"], int(rng.uniform(4, 6 + 60 * lvl)))
        elif kind == "lowres":
            p["scale"] = min(p["scale"], max(0.10, 1.0 - lvl * rng.uniform(0.70, 0.92)))
        elif kind == "uneven_light":
            p["illum"] = max(p["illum"], 0.25 + 0.70 * lvl)
        elif kind == "glare":
            p["glare_n"] = max(p["glare_n"], rng.choice([1, 1, 2]))
            p["glare_s"] = max(p["glare_s"], 0.5 + 1.1 * lvl)
        elif kind == "lowcontrast":
            p["contrast"] = min(p["contrast"], 1.0 - 0.80 * lvl)
        elif kind == "angle":
            p["theta"] = max(p["theta"], 8 + 62 * lvl)
        elif kind == "occlusion":
            p["occ"] = max(p["occ"], 0.04 + 0.5 * lvl)
        elif kind == "noise":
            p["noise"] = max(p["noise"], 3 + 24 * lvl)
            p["jpeg"] = int(max(15, 80 - 60 * lvl))

    if cond == "clean":
        add("noise", 0.02)
        p["noise"] = rng.uniform(1.0, 3.0)
    elif cond == "combined":
        kinds = rng.sample(["blur", "lowres", "uneven_light", "glare", "lowcontrast", "angle",
                            "occlusion", "noise"], rng.choice([2, 3]))
        for k in kinds:
            add(k, rng.uniform(0.15, 0.65))
    elif cond == "severe":
        kinds = rng.sample(["blur", "lowres", "glare", "lowcontrast", "angle", "occlusion"],
                           rng.choice([2, 3]))
        for k in kinds:
            add(k, rng.uniform(0.6, 1.0))
    else:
        add(cond, rng.uniform(0.0, 1.0))
    return p


def degrade(img, mask, p, rng, rng_np, text_center):
    """Apply degradation params to a clean render. Returns (uint8 BGR image, aligned ink mask,
    measured legibility factors)."""
    H, W = img.shape[:2]
    img = img.copy()
    mask_t = mask.copy()
    # 1. geometry
    Hm = _homography(W, H, p["theta"], p["inplane"])
    # keep the whole inscription inside the frame (camera "moves back" if needed): no truncation
    ys0, xs0 = np.nonzero(mask > 0.5)
    if len(xs0):
        poly = np.float32([[xs0.min(), ys0.min()], [xs0.max(), ys0.min()], [xs0.max(), ys0.max()],
                           [xs0.min(), ys0.max()]]).reshape(-1, 1, 2)
        tp = cv2.perspectiveTransform(poly, Hm).reshape(-1, 2)
        ext = np.abs(tp - [W / 2, H / 2]).max(axis=0)
        s = float(min(1.0, (W / 2 - 6) / max(ext[0], 1), (H / 2 - 6) / max(ext[1], 1)))
        if s < 1.0:
            S = np.array([[s, 0, W / 2 * (1 - s)], [0, s, H / 2 * (1 - s)], [0, 0, 1]], np.float64)
            Hm = S @ Hm
    img = cv2.warpPerspective(img, Hm, (W, H), borderMode=cv2.BORDER_REFLECT)
    mask_t = cv2.warpPerspective(mask_t, Hm, (W, H), borderMode=cv2.BORDER_CONSTANT)
    # 2. uneven illumination (multiplicative linear ramp + vignette)
    gain_text = 1.0
    if p["illum"] > 0:
        ang = rng.uniform(0, 2 * np.pi)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        ramp = ((xx / W - 0.5) * np.cos(ang) + (yy / H - 0.5) * np.sin(ang))
        ramp = ramp / (np.abs(ramp).max() + 1e-6)
        vig = 1 - 0.5 * (((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2) / 0.5)
        field = (1 + 0.9 * p["illum"] * ramp) * (1 - p["illum"] * 0.5 * (1 - vig))
        field = np.clip(field, 0.08, 1.8)
        img *= field[..., None]
        _ink = mask_t > 0.5
        gain_text = float(field[_ink].mean()) if _ink.sum() else 1.0
    # 3. low contrast
    if p["contrast"] < 1.0:
        m = img.mean()
        img = m + (img - m) * p["contrast"]
    # 4. glare
    glare_overlap = 0.0
    if p["glare_n"] > 0:
        g = _glare_field((H, W), p["glare_n"], p["glare_s"], rng, rng_np, near=text_center)
        img = img + g[..., None] * 255.0 * 0.9
        ink = mask_t > 0.5
        if ink.sum() > 0:
            glare_overlap = float(((img.mean(axis=2) > 245) & ink).sum() / ink.sum())
    img = np.clip(img, 0, 255)
    # 5. occlusion (dark opaque blob/finger/dirt patches over the text)
    occ_frac = 0.0
    if p["occ"] > 0:
        occ = np.zeros((H, W), np.uint8)
        ys, xs = np.nonzero(mask_t > 0.5)
        if len(xs):
            x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
            target = p["occ"]
            for _ in range(40):
                cx = rng.uniform(x0, x1); cy = rng.uniform(y0 - 5, y1 + 5)
                ax = rng.uniform(0.05, 0.18) * (x1 - x0 + 1); ay = rng.uniform(0.3, 1.0) * (y1 - y0 + 1)
                cv2.ellipse(occ, (int(cx), int(cy)), (max(int(ax), 2), max(int(ay), 2)),
                            rng.uniform(0, 180), 0, 360, 255, -1)
                cover = ((occ > 0) & (mask_t > 0.5)).sum() / max((mask_t > 0.5).sum(), 1)
                if cover >= target:
                    break
            occ = cv2.GaussianBlur(occ, (0, 0), 1.5)
            col = np.array([rng.uniform(20, 70)] * 3, np.float32)
            a = (occ.astype(np.float32) / 255.0)[..., None]
            img = img * (1 - a) + col[None, None, :] * a
            occ_frac = float(((occ > 127) & (mask_t > 0.5)).sum() / max((mask_t > 0.5).sum(), 1))
    # 6. blur
    sigma_equiv = p["blur_sigma"]
    if p["blur_sigma"] > 0:
        img = cv2.GaussianBlur(img, (0, 0), p["blur_sigma"])
    if p["motion_len"] > 1:
        L = int(p["motion_len"])
        k = np.zeros((L, L), np.float32); k[L // 2, :] = 1.0 / L
        ang = rng.uniform(0, 180)
        Rm = cv2.getRotationMatrix2D((L / 2 - 0.5, L / 2 - 0.5), ang, 1.0)
        k = cv2.warpAffine(k, Rm, (L, L)); k /= max(k.sum(), 1e-6)
        img = cv2.filter2D(img, -1, k)
        sigma_equiv = max(sigma_equiv, L / 3.0)
    # 7. resolution reduction (true downsampling: image gets smaller, like a lower-res sensor/farther)
    scale = p["scale"]
    if scale < 0.999:
        nw, nh = max(int(W * scale), 24), max(int(H * scale), 16)
        img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
        mask_t = cv2.resize(mask_t, (nw, nh), interpolation=cv2.INTER_AREA)
    # measured factors (before sensor noise)
    gray = img.mean(axis=2)
    ink = mask_t > 0.5
    ys, xs = np.nonzero(ink)
    if len(xs) < 5:
        h_eff, bbox = 0.0, (0, 0, 1, 1)
    else:
        h_eff = float(ys.max() - ys.min() + 1)
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    # legibility-relevant contrast: generator contrast scale x local illumination gain at the text.
    # (A raw ink/background luminance difference is NOT used: embossed relief is legible through edge
    #  shading although its mean-luminance difference is ~0.)
    contrast_ink = float(p["contrast"] * min(gain_text, 1.0))
    # 8. sensor noise + JPEG
    if p["noise"] > 0:
        img = img + rng_np.normal(0, p["noise"], img.shape).astype(np.float32)
    img = np.clip(img, 0, 255).astype(np.uint8)
    ok, enc = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, int(p["jpeg"])])
    img = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    meas = dict(h_eff=h_eff, contrast_ink=contrast_ink, glare_overlap=glare_overlap,
                occ_frac=occ_frac, sigma_equiv=float(sigma_equiv), scale=float(scale),
                cos_theta=float(np.cos(np.deg2rad(p["theta"]))), illum=float(p["illum"]),
                noise=float(p["noise"]), ink_lum_diff=_ink_contrast(gray, mask_t))
    return img, mask_t, bbox, meas


def legibility_labels(meas, stroke_px):
    """Generator-defined readability proxy (thresholds fixed a priori from clean-render statistics;
    NOT tuned against OCR output; NOT validated by human annotators)."""
    stroke_eff = max(stroke_px * meas["scale"], 0.5)
    blur_ratio = (meas["sigma_equiv"] * meas["scale"] + 0.5) / stroke_eff
    m = dict(meas); m["blur_ratio"] = float(blur_ratio)
    unread = (blur_ratio >= 1.3 or m["h_eff"] < 10 or m["contrast_ink"] < 0.15
              or m["glare_overlap"] >= 0.40 or m["occ_frac"] >= 0.30 or m["cos_theta"] < 0.35)
    read = (blur_ratio <= 0.7 and m["h_eff"] >= 20 and m["contrast_ink"] >= 0.50 and m["noise"] <= 14
            and m["glare_overlap"] <= 0.10 and m["occ_frac"] <= 0.05 and m["cos_theta"] >= 0.60)
    label = "unreadable" if unread else ("readable" if read else "partial")

    def lvl(v, a, b, higher_bad=True):
        if higher_bad:
            return "good" if v <= a else ("moderate" if v <= b else "poor")
        return "good" if v >= a else ("moderate" if v >= b else "poor")

    q = dict(q_blur=lvl(blur_ratio, 0.5, 1.0), q_glare=lvl(m["glare_overlap"], 0.03, 0.2),
             q_resolution=lvl(m["h_eff"], 30, 18, False), q_contrast=lvl(m["contrast_ink"], 0.6, 0.3, False),
             q_lighting=lvl(m["illum"], 0.15, 0.5), q_occlusion=lvl(m["occ_frac"], 0.02, 0.15),
             q_viewing=lvl(m["cos_theta"], 0.8, 0.55, False))
    return label, m, q


def build_item_specs(cfg, seed=None):
    seed = cfg["seed"] if seed is None else seed
    rng = random.Random(seed)
    specs = []
    n_per = cfg["dataset"]["items_per_source"]
    ratios = cfg["dataset"]["split_ratios"]
    for sname in cfg["dataset"]["sources"]:
        src = SOURCES[sname]
        idx = list(range(n_per)); rng.shuffle(idx)
        n_tr = int(round(n_per * ratios["train"])); n_va = int(round(n_per * ratios["val"]))
        for j in range(n_per):
            split = "train" if idx[j] < n_tr else ("val" if idx[j] < n_tr + n_va else "test")
            specs.append(dict(item_id=f"{sname}-{j:03d}", source=sname, split=split,
                              text=make_text(rng), style=rng.choice(STYLES),
                              font_path=rng.choice(src["fonts"]), cap_h=rng.randint(52, 74),
                              seed=rng.randint(0, 2 ** 31 - 1)))
    return specs


def render_acquisition(spec, cond, acq_seed, size=(640, 400), params=None):
    """Full acquisition: clean render + degradation. Returns image & annotation dict."""
    img, mask = render_clean(spec, size)
    rng = random.Random(acq_seed); rng_np = np.random.default_rng(acq_seed)
    p = params if params is not None else sample_degradation(cond, rng)
    ys, xs = np.nonzero(mask > 0.5)
    center = (float(xs.mean()), float(ys.mean())) if len(xs) else (size[0] / 2, size[1] / 2)
    out, mask_t, bbox, meas = degrade(img, mask, p, rng, rng_np, center)
    stroke = _stroke_width(mask)
    label, m, q = legibility_labels(meas, stroke)
    ann = dict(condition=cond, params=json.dumps(p), bbox=list(bbox), readability=label,
               stroke_px=stroke, **{k: m[k] for k in ("blur_ratio", "h_eff", "contrast_ink",
                                                      "glare_overlap", "occ_frac", "cos_theta", "scale", "noise")}, **q)
    return out, ann
