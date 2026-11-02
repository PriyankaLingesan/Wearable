"""No-reference image-quality features (cheap, CPU-only, wearable-friendly).

Focus: variance of the Laplacian (Pech-Pacheco et al., ICPR 2000) and Tenengrad gradient energy.
Text-region sharpness: standard deviation of Sobel gradient magnitude on the ROI, inspired by
CG-DIQA (Li et al., arXiv:1807.04047) but computed on the localised ROI rather than MSER regions.
"""
import cv2
import numpy as np


def _gray(img):
    return img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def lap_var(g):
    return float(cv2.Laplacian(g, cv2.CV_64F).var())


def tenengrad(g):
    gx = cv2.Sobel(g, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_64F, 0, 1, ksize=3)
    return float(np.mean(gx * gx + gy * gy))


def noise_sigma(g):
    """Immerkaer fast noise-variance estimate."""
    k = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], np.float64)
    h, w = g.shape
    s = np.abs(cv2.filter2D(g.astype(np.float64), -1, k)[1:-1, 1:-1]).sum()
    return float(s * np.sqrt(0.5 * np.pi) / (6.0 * (w - 2) * (h - 2)))


def illum_nonuniformity(g, n=6):
    h, w = g.shape
    bh, bw = max(h // n, 1), max(w // n, 1)
    means = np.array([g[i * bh:(i + 1) * bh, j * bw:(j + 1) * bw].mean()
                      for i in range(n) for j in range(n)])
    return float(means.std() / (means.mean() + 1e-6))


def frame_features(img):
    g = _gray(img)
    gf = g.astype(np.float32)
    p1, p5, p95, p99 = np.percentile(gf, [1, 5, 95, 99])
    return {
        "f_lapvar_log": float(np.log1p(lap_var(g))),
        "f_tenengrad_log": float(np.log1p(tenengrad(g))),
        "f_bright": float(gf.mean() / 255.0),
        "f_contrast_rms": float(gf.std() / 255.0),
        "f_dynrange": float((p99 - p1) / 255.0),
        "f_illum_nonuni": illum_nonuniformity(gf),
        "f_sat_frac": float((g >= 250).mean()),
        "f_dark_frac": float((g <= 12).mean()),
        "f_noise": noise_sigma(g),
        "f_min_side": float(min(g.shape)),
    }


def roi_features(gray_roi):
    g = gray_roi
    if g.size < 64:
        return {k: 0.0 for k in ("r_lapvar_log", "r_tenengrad_log", "r_cg_grad_std", "r_contrast",
                                 "r_sat_frac", "r_illum_nonuni", "r_height", "r_width", "r_noise")}
    gf = g.astype(np.float32)
    gx = cv2.Sobel(gf, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gf, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(gx * gx + gy * gy)
    p5, p95 = np.percentile(gf, [5, 95])
    return {
        "r_lapvar_log": float(np.log1p(lap_var(g))),
        "r_tenengrad_log": float(np.log1p(tenengrad(g))),
        "r_cg_grad_std": float(mag.std() / 255.0),
        "r_contrast": float((p95 - p5) / 255.0),
        "r_sat_frac": float((g >= 250).mean()),
        "r_illum_nonuni": illum_nonuniformity(gf, 4),
        "r_height": float(g.shape[0]),
        "r_width": float(g.shape[1]),
        "r_noise": noise_sigma(g),
    }


QUALITY_FEATURES = ["f_lapvar_log", "f_tenengrad_log", "f_bright", "f_contrast_rms", "f_dynrange",
                    "f_illum_nonuni", "f_sat_frac", "f_dark_frac", "f_noise", "f_min_side",
                    "r_lapvar_log", "r_tenengrad_log", "r_cg_grad_std", "r_contrast", "r_sat_frac",
                    "r_illum_nonuni", "r_height", "r_width", "r_noise", "loc_score", "roi_area_frac"]
