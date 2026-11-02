"""Feature assembly, calibrated rejector, readability classifier wrappers and recapture guidance."""
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import (ExtraTreesClassifier, GradientBoostingClassifier, RandomForestClassifier)
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from . import metrics as M
from . import quality as Q
from .pipeline import grammar_valid, norm_edit

QUALITY = Q.QUALITY_FEATURES
OCR_CONF = ["p_conf"]
OCR_UNC = ["p_conf", "p_conf_min", "s_conf", "disagree", "agree_exact", "p_len", "s_len", "p_ntok", "p_empty"]
GRAMMAR = ["p_grammar", "s_grammar"]

FEATURE_SETS = {
    "quality_only": QUALITY,
    "ocr_unc_only": OCR_UNC,
    "quality+ocr_unc": QUALITY + OCR_UNC,
    "quality+ocr_unc+grammar": QUALITY + OCR_UNC + GRAMMAR,
}


def assemble(raw, man, primary, secondary):
    """Merge manifest + pipeline outputs into one modelling table.
    primary/secondary = (engine, variant) tuples. Adds uncertainty features and the correctness target."""
    df = man.merge(raw, on="image_id", how="inner")
    return assemble_merged(df, primary, secondary)


def assemble_merged(df, primary, secondary):
    """Same as `assemble` for an already merged table (used for the controlled sweeps)."""
    pe, pv = primary
    se, sv = secondary
    rows = []
    for _, r in df.iterrows():
        p = dict(text=r[f"{pe}_{pv}_text"] if isinstance(r[f"{pe}_{pv}_text"], str) else "", conf=r[f"{pe}_{pv}_conf"],
                 conf_min=r[f"{pe}_{pv}_confmin"], n_tokens=r[f"{pe}_{pv}_ntok"])
        s = dict(text=r[f"{se}_{sv}_text"] if isinstance(r[f"{se}_{sv}_text"], str) else "", conf=r[f"{se}_{sv}_conf"],
                 conf_min=r[f"{se}_{sv}_confmin"], n_tokens=r[f"{se}_{sv}_ntok"])
        u = {"p_conf": p["conf"], "p_conf_min": p["conf_min"], "p_len": float(len(p["text"].replace(" ", ""))),
             "p_ntok": float(p["n_tokens"]), "s_conf": s["conf"], "s_len": float(len(s["text"].replace(" ", ""))),
             "disagree": norm_edit(p["text"].replace(" ", ""), s["text"].replace(" ", "")),
             "agree_exact": float(p["text"].replace(" ", "") == s["text"].replace(" ", "")),
             "p_grammar": float(grammar_valid(p["text"])), "s_grammar": float(grammar_valid(s["text"])),
             "p_empty": float(len(p["text"]) == 0), "pred_text": p["text"], "sec_text": s["text"]}
        rows.append(u)
    U = pd.DataFrame(rows, index=df.index)
    df = pd.concat([df, U], axis=1)
    df["correct"] = [M.exact(g, p) for g, p in zip(df["text"], df["pred_text"])]
    df["cer"] = [M.cer(g, p) for g, p in zip(df["text"], df["pred_text"])]
    return df


# ---------------- model zoo ----------------
def readability_zoo(seed=0):
    return {
        "SVM-RBF": make_pipeline(StandardScaler(), SVC(C=3.0, gamma="scale", probability=True, random_state=seed)),
        "RandomForest": RandomForestClassifier(300, min_samples_leaf=2, random_state=seed, n_jobs=1),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.08, random_state=seed),
        "ExtraTrees": ExtraTreesClassifier(400, min_samples_leaf=2, random_state=seed, n_jobs=1),
        "LogReg": make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000)),
        "kNN": make_pipeline(StandardScaler(), KNeighborsClassifier(15)),
        "MLP": make_pipeline(StandardScaler(), MLPClassifier((64, 32), alpha=1e-3, max_iter=800, random_state=seed)),
    }


def rejector_zoo(seed=0):
    return {
        "LogReg": make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=3000)),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=120, max_depth=3, learning_rate=0.06, subsample=0.8, random_state=seed),
        "RandomForest": RandomForestClassifier(300, min_samples_leaf=4, random_state=seed, n_jobs=1),
        "ExtraTrees": ExtraTreesClassifier(400, min_samples_leaf=4, random_state=seed, n_jobs=1),
    }


class CalibratedRejector:
    """Separated rejector (Hendrickx et al. taxonomy): base model -> P(transcription correct), then isotonic
    calibration fitted on out-of-fold scores. `score(X)` returns calibrated probabilities. Threshold tau is
    chosen on out-of-fold development scores for a target accepted-error rate."""

    def __init__(self, base, features, n_splits=5):
        self.base, self.features, self.n_splits = base, list(features), n_splits
        self.iso = None; self.model = None; self.taus = {}

    def fit(self, X, y, groups, risk_targets=(0.01, 0.02, 0.05, 0.10)):
        Xf = X[self.features].values.astype(float); y = np.asarray(y, int)
        oof = np.zeros(len(y))
        for tr, te in GroupKFold(self.n_splits).split(Xf, y, groups):
            m = clone(self.base).fit(Xf[tr], y[tr])
            oof[te] = m.predict_proba(Xf[te])[:, 1]
        self.iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(oof, y)
        self.model = clone(self.base).fit(Xf, y)
        self.oof_cal = self.iso.predict(oof)
        self.oof_raw = oof
        self.taus = {str(t): M.threshold_for_risk(self.oof_cal, y, t) for t in risk_targets}
        self.taus_ucb = {str(t): M.threshold_for_risk_ucb(self.oof_cal, y, t) for t in risk_targets}
        return self

    def raw(self, X):
        return self.model.predict_proba(X[self.features].values.astype(float))[:, 1]

    def score(self, X):
        return self.iso.predict(self.raw(X))

    def decide(self, X, risk_target="0.05"):
        s = self.score(X); tau = self.taus[str(risk_target)]
        return s, s >= tau


def save(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(obj, path, compress=3)


# ---------------- recapture guidance ----------------
GUIDE = {
    "blur": "Image blurry - hold wrist steady, refocus.",
    "glare": "Glare on mark - tilt wrist, lower LED.",
    "dark": "Too dark / low contrast - raise LED.",
    "uneven": "Uneven light - re-centre under LED.",
    "small": "Mark too small - move camera closer.",
    "reposition": "Unclear read - re-align and retake.",
}
# Which manifest quality label(s) correspond to each guidance cause (for evaluating guidance correctness)
CAUSE_TO_LABELS = {"blur": ["q_blur"], "glare": ["q_glare"], "dark": ["q_contrast"], "uneven": ["q_lighting"],
                   "small": ["q_resolution"], "reposition": ["q_occlusion", "q_viewing"]}


class Guidance:
    """Rule-based diagnosis of the most likely capture problem. Reference statistics come from images labelled
    'readable' in the DEVELOPMENT split; the rule picks the factor with the largest standardised deficit."""

    def __init__(self):
        self.ref = {}

    def fit(self, df):
        good = df[df["readability"] == "readable"]
        for k in ["r_lapvar_log", "r_contrast", "r_height", "f_illum_nonuni", "r_sat_frac", "f_bright", "r_tenengrad_log"]:
            self.ref[k] = (float(good[k].mean()), float(good[k].std() + 1e-6))
        return self

    def z(self, k, v):
        m, s = self.ref[k]
        return (v - m) / s

    def diagnose(self, f):
        d = {"blur": -min(self.z("r_lapvar_log", f["r_lapvar_log"]), self.z("r_tenengrad_log", f["r_tenengrad_log"])),
             "glare": self.z("r_sat_frac", f["r_sat_frac"]) + (2.0 if f["f_sat_frac"] > 0.02 else 0.0),
             "dark": -min(self.z("r_contrast", f["r_contrast"]), self.z("f_bright", f["f_bright"])),
             "uneven": self.z("f_illum_nonuni", f["f_illum_nonuni"]),
             "small": -self.z("r_height", f["r_height"])}
        cause, val = max(d.items(), key=lambda kv: kv[1])
        if val < 1.0:
            cause = "reposition"
        return cause, GUIDE[cause], d
