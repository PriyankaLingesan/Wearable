"""Build every result table (CSV + Markdown) and figure from the executed experiments. Nothing here invents data:
all numbers are read from results/*.csv|json produced by scripts 01-05,07."""
import json
import os
import sys
import warnings

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hallmark import ROOT, CFG  # noqa: E402
from hallmark import metrics as M  # noqa: E402
from hallmark import models as MD  # noqa: E402

R = os.path.join(ROOT, "results"); T = os.path.join(R, "tables"); F = os.path.join(ROOT, "figures")
os.makedirs(T, exist_ok=True); os.makedirs(F, exist_ok=True)
OI = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000", "#F0E442"]
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100,
                     "savefig.dpi": 200, "axes.prop_cycle": plt.cycler(color=OI), "legend.frameon": False})
LABELS = ["readable", "partial", "unreadable"]


def save_table(df, name, floatfmt=3):
    df.to_csv(os.path.join(T, name + ".csv"), index=False)
    with open(os.path.join(T, name + ".md"), "w") as f:
        f.write(df.round(floatfmt).to_markdown(index=False) if hasattr(df, "to_markdown") else df.round(floatfmt).to_string(index=False))
    return df


def load_all():
    man = pd.read_csv(os.path.join(ROOT, "data", "manifest.csv"))
    raw = pd.read_csv(os.path.join(R, "ocr_raw.csv"))
    dep = json.load(open(os.path.join(ROOT, "models", "deployment.json")))
    primary, secondary = tuple(dep["primary"]), tuple(dep["secondary"])
    df = MD.assemble(raw, man, primary, secondary)
    return man, raw, df, dep, primary, secondary


def t_dataset(man):
    rows = []
    for sp in ("train", "val", "test"):
        d = man[man.split == sp]
        rows.append(dict(split=sp, items=d.item_id.nunique(), images=len(d), readable=(d.readability == "readable").sum(),
                         partial=(d.readability == "partial").sum(), unreadable=(d.readability == "unreadable").sum()))
    d = man
    rows.append(dict(split="total", items=d.item_id.nunique(), images=len(d), readable=(d.readability == "readable").sum(),
                     partial=(d.readability == "partial").sum(), unreadable=(d.readability == "unreadable").sum()))
    save_table(pd.DataFrame(rows), "T1_dataset_splits")
    c = man.groupby(["condition", "readability"]).size().unstack(fill_value=0).reset_index()
    save_table(c, "T1b_dataset_conditions")
    s = man.groupby(["source", "style"]).size().unstack(fill_value=0).reset_index()
    save_table(s, "T1c_dataset_sources_styles")


def fig_examples(man):
    rng = np.random.default_rng(3)
    test = man[man.split == "test"]
    picks = []
    for cond in ["clean", "blur", "lowres", "uneven_light", "glare", "lowcontrast", "angle", "occlusion", "severe"]:
        d = test[test.condition == cond]
        picks.append(d.iloc[int(rng.integers(0, len(d)))])
    for st in ["engraved", "embossed", "stamped", "laser"]:
        d = test[(test.condition == "clean") & (test["style"] == st)]
        if len(d) == 0:  # not every style has a clean test acquisition; fall back to the mildest available condition
            d = test[(test["style"] == st) & (test.readability == "readable")]
        if len(d) == 0:
            d = test[test["style"] == st]
        picks.append(d.iloc[int(rng.integers(0, len(d)))])
    fig, axs = plt.subplots(3, 5, figsize=(10, 5.2))
    for ax, r in zip(axs.ravel(), picks):
        im = cv2.cvtColor(cv2.imread(os.path.join(ROOT, "data", r.path)), cv2.COLOR_BGR2RGB)
        ax.imshow(im); ax.axis("off")
        ax.set_title(f"{r.condition} | {r["style"]}\nGT '{r.text}' | {r.readability}", fontsize=6.5)
    for ax in axs.ravel()[len(picks):]:
        ax.axis("off")
    fig.suptitle("Examples from the SYNTHETIC dataset (procedural renderings - not photographs of real jewellery)", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(F, "fig_dataset_examples.png")); plt.close(fig)


def t_ocr(raw, man, df, primary):
    d = man.merge(raw, on="image_id"); test = d[d.split == "test"]; dev = d[d.split != "test"]
    rows = []
    for e in ("tesseract", "rapidocr"):
        for v in ("raw", "red", "enh", "bin", "oracleraw", "oracleenh"):
            col = f"{e}_{v}_text"
            if col not in test:
                continue
            s = M.ocr_summary(test["text"], test[col].fillna(""))
            sd = M.ocr_summary(dev["text"], dev[col].fillna(""))
            rows.append(dict(engine=e, input=("GT-box ROI, " + v[6:]) if v.startswith("oracle") else ("detected ROI, " + v),
                             test_CER=s["CER"], test_WER=s["WER"], test_exact=s["exact"], test_exact_strict=s["exact_strict"],
                             dev_exact=sd["exact"], dev_CER=sd["CER"]))
    t = save_table(pd.DataFrame(rows), "T2_ocr_baseline_and_preprocessing")
    # per-condition and per-style (test) for the two engines with the selected variant
    pe, pv = primary
    rows = []
    for cond, g in test.groupby("condition"):
        r = dict(condition=cond, n=len(g))
        for e in ("tesseract", "rapidocr"):
            r[f"{e}_raw_exact"] = M.ocr_summary(g["text"], g[f"{e}_raw_text"].fillna(""))["exact"]
            r[f"{e}_raw_CER"] = M.ocr_summary(g["text"], g[f"{e}_raw_text"].fillna(""))["CER"]
        r["rapidocr_enh_exact"] = M.ocr_summary(g["text"], g["rapidocr_enh_text"].fillna(""))["exact"]
        r["tesseract_enh_exact"] = M.ocr_summary(g["text"], g["tesseract_enh_text"].fillna(""))["exact"]
        rows.append(r)
    bc = save_table(pd.DataFrame(rows), "T3_ocr_by_condition")
    rows = []
    for st, g in test[test.condition == "clean"].groupby("style"):
        rows.append(dict(style=st, n=len(g), rapidocr_raw_exact=M.ocr_summary(g["text"], g["rapidocr_raw_text"].fillna(""))["exact"],
                         tesseract_raw_exact=M.ocr_summary(g["text"], g["tesseract_raw_text"].fillna(""))["exact"]))
    save_table(pd.DataFrame(rows), "T3b_ocr_by_style_clean")
    # figure
    fig, ax = plt.subplots(figsize=(8, 3.2))
    w = 0.2; x = np.arange(len(bc))
    for i, (c, lab) in enumerate([("rapidocr_raw_exact", "RapidOCR raw ROI"), ("rapidocr_enh_exact", "RapidOCR enhanced"),
                                  ("tesseract_raw_exact", "Tesseract raw ROI"), ("tesseract_enh_exact", "Tesseract enhanced")]):
        ax.bar(x + (i - 1.5) * w, bc[c], w, label=lab)
    ax.set_xticks(x); ax.set_xticklabels(bc.condition, rotation=30, ha="right"); ax.set_ylabel("exact transcription accuracy")
    ax.set_title("OCR accuracy by acquisition condition (test split, detected ROI)"); ax.legend(ncol=2, fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(F, "fig_ocr_by_condition.png")); plt.close(fig)
    return t


def t_ablation(man):
    p = os.path.join(R, "ablation_raw.csv")
    if not os.path.exists(p):
        return
    ab = pd.read_csv(p).merge(man[["image_id", "text"]], on="image_id")
    cfgs = [c.split("|")[1] for c in ab.columns if c.startswith("rapidocr|")]
    rows = []
    for c in cfgs:
        r = dict(config=c)
        for e in ("rapidocr", "tesseract"):
            s = M.ocr_summary(ab["text"], ab[f"{e}|{c}"].fillna(""))
            r[f"{e}_CER"] = s["CER"]; r[f"{e}_exact"] = s["exact"]
        rows.append(r)
    t = save_table(pd.DataFrame(rows), "T4_enhancement_ablation")
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.2), sharey=True)
    for ax, e in zip(axs, ("rapidocr", "tesseract")):
        ax.barh(t.config, t[f"{e}_exact"], color=OI[0] if e == "rapidocr" else OI[1]); ax.invert_yaxis()
        ax.axvline(t[f"{e}_exact"].iloc[0], color="k", lw=0.8, ls="--"); ax.set_title(e); ax.set_xlabel("exact accuracy (test)")
    fig.suptitle("Enhancement-step ablation on the detected ROI (dashed = no enhancement)", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(F, "fig_ablation.png")); plt.close(fig)


def t_sweeps(dep, primary, secondary):
    p = os.path.join(R, "sweeps_raw.csv")
    if not os.path.exists(p):
        return
    sw = pd.read_csv(p)
    sw["image_id"] = [f"{a}_{l}_{i}" for a, l, i in zip(sw.axis, sw.level, sw.item_id)]
    sw["condition"] = sw["axis"]
    dfm = MD.assemble_merged(sw.copy(), primary, secondary)
    import joblib
    rej = joblib.load(os.path.join(ROOT, "models", "rejector.joblib")); R_ = rej["rejector"]; tau = rej["taus"]["0.05"]
    dfm["p"] = R_.score(dfm); dfm["accepted"] = dfm["p"] >= tau
    rows = []
    for (axis, lv), g in dfm.groupby(["axis", "level"], sort=False):
        r = dict(axis=axis, level=lv, n=len(g))
        for e in ("rapidocr", "tesseract"):
            for v in ("raw", "enh"):
                s = M.ocr_summary(g["text"], g[f"{e}_{v}_text"].fillna(""))
                r[f"{e}_{v}_exact"] = s["exact"]; r[f"{e}_{v}_CER"] = s["CER"]
        r["primary_exact"] = g["correct"].mean()
        r["mean_p_correct"] = g["p"].mean()
        r["coverage_at_5pct_target"] = g["accepted"].mean()
        r["accepted_error_rate"] = (1 - g.loc[g.accepted, "correct"].mean()) if g.accepted.sum() else np.nan
        r["accepted_errors"] = int((~g.loc[g.accepted, "correct"].astype(bool)).sum())
        r["loc_iou_ge_0_5"] = (g["sweep_loc_iou"] >= 0.5).mean()
        r["frame_lapvar_log"] = g["f_lapvar_log"].mean()
        rows.append(r)
    t = save_table(pd.DataFrame(rows), "T5_robustness_sweeps")
    names = {"blur": "Gaussian blur sigma (px)", "lighting": "illumination non-uniformity", "glare": "glare strength",
             "resolution": "resolution scale", "angle": "viewing angle (deg)"}
    fig, axs = plt.subplots(2, 3, figsize=(10, 5.4))
    for ax, (axis, g) in zip(axs.ravel(), t.groupby("axis", sort=False)):
        x = g["level"].values
        ax.plot(x, g.rapidocr_raw_exact, "o-", label="RapidOCR raw", color=OI[0])
        ax.plot(x, g.rapidocr_enh_exact, "s--", label="RapidOCR enhanced", color=OI[2])
        ax.plot(x, g.tesseract_raw_exact, "^-", label="Tesseract raw", color=OI[1])
        ax.plot(x, g.coverage_at_5pct_target, "d:", label="rejector coverage (5% target)", color=OI[3])
        ax.set_title(names[axis]); ax.set_ylim(-0.02, 1.02); ax.set_ylabel("accuracy / coverage")
        if axis == "resolution":
            ax.invert_xaxis()
    axs.ravel()[-1].axis("off")
    h, l = axs.ravel()[0].get_legend_handles_labels(); axs.ravel()[-1].legend(h, l, loc="center", fontsize=8)
    fig.suptitle("Controlled single-factor robustness sweeps (48 test items per level; synthetic)", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(F, "fig_sweeps.png")); plt.close(fig)


def fig_confusion():
    rd = json.load(open(os.path.join(R, "readability_results.json")))
    rows = []
    for fs, v in rd.items():
        t = v["test"]
        rows.append(dict(feature_set=fs, selected_model=v["selected"], accuracy=t["accuracy"], precision_macro=t["precision_macro"],
                         recall_macro=t["recall_macro"], f1_macro=t["f1_macro"]))
    save_table(pd.DataFrame(rows), "T6_readability_test")
    cv = pd.DataFrame([r for v in rd.values() for r in v["cv"]])
    save_table(cv[["feature_set", "model", "cv_f1_mean", "cv_f1_sd", "cv_acc_mean"]], "T6b_readability_cv_dev")
    allm = pd.DataFrame([dict(feature_set=fs, model=m, **s) for fs, v in rd.items() for m, s in v["test_all_models"].items()])
    save_table(allm, "T6c_readability_all_models_test")
    pc = pd.DataFrame([dict(feature_set=fs, cls=c, **vv) for fs, v in rd.items() for c, vv in v["test"]["per_class"].items()])
    save_table(pc, "T6d_readability_per_class")
    for fs, v in rd.items():
        cm = np.array(v["test"]["confusion"]); fig, ax = plt.subplots(figsize=(3.6, 3.2))
        ax.imshow(cm, cmap="Blues")
        for i in range(3):
            for j in range(3):
                ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black")
        ax.set_xticks(range(3)); ax.set_yticks(range(3)); ax.set_xticklabels(LABELS, rotation=25); ax.set_yticklabels(LABELS)
        ax.set_xlabel("predicted"); ax.set_ylabel("generator-defined label")
        ax.set_title(f"{fs} ({v['selected']})\nacc {v['test']['accuracy']:.2f}  macro-F1 {v['test']['f1_macro']:.2f}", fontsize=8)
        fig.tight_layout(); fig.savefig(os.path.join(F, f"fig_confusion_{fs.replace('+', '_')}.png")); plt.close(fig)


def fig_rejection():
    rj = json.load(open(os.path.join(R, "rejection_results.json")))["results"]
    paired = rj.pop("_paired_delta_aurc", {})
    ts = pd.read_csv(os.path.join(R, "test_scores.csv"))
    save_table(pd.DataFrame([dict(comparison=k, delta_AURC=v["mean"], CI95=f"[{v['ci_lo']:+.3f}, {v['ci_hi']:+.3f}]",
                                  excludes_zero=bool(v["ci_lo"] > 0 or v["ci_hi"] < 0)) for k, v in paired.items()]), "T7b_paired_delta_aurc")
    cols = {"S1": "S1 OCR conf (raw)", "S2": "S2 rule gate + OCR conf", "S3": "S3 OCR-uncertainty only", "S4": "S4 quality only",
            "S5": "S5 quality + OCR-uncertainty", "S6": "S6 + grammar (ablation)"}
    rows = []
    for k, v in rj.items():
        r = dict(strategy=k, AURC=v["aurc"], E_AURC=v["eaurc"], risk_at_cov50=v["risk_at_cov_50"], risk_at_cov70=v["risk_at_cov_70"],
                 risk_at_cov90=v["risk_at_cov_90"], ECE=v.get("ece"), Brier=v.get("brier"))
        if "aurc_ci" in v:
            r["AURC_CI"] = f"[{v['aurc_ci']['ci_lo']:.3f}, {v['aurc_ci']['ci_hi']:.3f}]"
        if "delta_aurc_vs_S1" in v:
            d = v["delta_aurc_vs_S1"]; r["dAURC_vs_S1"] = f"{d['mean']:+.3f} [{d['ci_lo']:+.3f}, {d['ci_hi']:+.3f}]"
        rows.append(r)
    save_table(pd.DataFrame(rows), "T7_rejection_aurc")
    rows = []
    for k, v in rj.items():
        for t, a in v["at_target"].items():
            rows.append(dict(strategy=k, target_accepted_error=float(t), tau=a["tau"] if np.isfinite(a["tau"]) else np.nan, test_coverage=a["coverage"],
                             test_rejection_rate=a["rejection_rate"], test_accepted_error=a["accepted_error_rate"], accepted=a["accepted"],
                             accepted_errors=a["accepted_errors"]))
    save_table(pd.DataFrame(rows), "T8_rejection_operating_points")
    rows = []
    for k, v in rj.items():
        for t, a in v["at_target_ucb"].items():
            rows.append(dict(strategy=k, target_accepted_error=float(t), tau=a["tau"] if np.isfinite(a["tau"]) else np.nan, test_coverage=a["coverage"],
                             test_rejection_rate=a["rejection_rate"], test_accepted_error=a["accepted_error_rate"], accepted=a["accepted"],
                             accepted_errors=a["accepted_errors"]))
    save_table(pd.DataFrame(rows), "T8b_rejection_operating_points_ucb")
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.6))
    y = ts["correct"].values
    for i, (c, lab) in enumerate(cols.items()):
        col = "score_" + c
        cov, risk = M.risk_coverage(ts[col].values, y)
        axs[0].plot(cov, risk, label=f"{lab} (AURC {M.aurc(ts[col].values, y):.3f})", color=OI[i], lw=1.6 if c in ("S1", "S5") else 1.0)
    cov, risk = M.risk_coverage(y.astype(float), y)
    axs[0].plot(cov, risk, "k:", lw=0.8, label="oracle ranking")
    axs[0].set_xlabel("coverage (fraction accepted)"); axs[0].set_ylabel("selective risk (accepted-error rate)")
    axs[0].set_title("Risk-coverage curves (test)"); axs[0].legend(fontsize=6.2, loc="upper left")
    # reliability
    bins = np.linspace(0, 1, 11)
    for i, (c, lab) in enumerate([("S1", "raw OCR confidence"), ("S5", "calibrated S5")]):
        p = np.clip(ts["score_" + c].values, 0, 1); xs, ys = [], []
        for lo, hi in zip(bins[:-1], bins[1:]):
            m = (p >= lo) & (p < hi if hi < 1 else p <= hi)
            if m.sum() >= 5:
                xs.append(p[m].mean()); ys.append(y[m].mean())
        axs[1].plot(xs, ys, "o-", label=f"{lab}  ECE {M.ece(p, y):.3f}", color=OI[0] if c == "S1" else OI[4])
    axs[1].plot([0, 1], [0, 1], "k:", lw=0.8); axs[1].set_xlabel("predicted P(correct)"); axs[1].set_ylabel("observed accuracy")
    axs[1].set_title("Reliability (test)"); axs[1].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(F, "fig_risk_coverage_calibration.png")); plt.close(fig)


def t_loso():
    p = os.path.join(R, "loso_results.json")
    if not os.path.exists(p):
        return
    L = json.load(open(p)); rows = []
    for s, v in L.items():
        d = v["delta_aurc"]
        rows.append(dict(held_out_source=s, n=v["n"], ocr_exact=v["ocr_exact"], AURC_S1=v["aurc_S1"], AURC_S5=v["aurc_S5"],
                         dAURC=f"{d['mean']:+.3f} [{d['ci_lo']:+.3f}, {d['ci_hi']:+.3f}]",
                         S1_cov_at_5=v["S1_at_0.05"]["coverage"], S1_err_at_5=v["S1_at_0.05"]["accepted_error_rate"],
                         S5_cov_at_5=v["S5_at_0.05"]["coverage"], S5_err_at_5=v["S5_at_0.05"]["accepted_error_rate"],
                         readability_acc=v["readability"]["accuracy"], readability_macroF1=v["readability"]["f1_macro"]))
    save_table(pd.DataFrame(rows), "T9_generalisation_leave_one_source_out")


def t_loc_sys():
    p = os.path.join(R, "localisation_benchmark.csv")
    if os.path.exists(p):
        save_table(pd.read_csv(p), "T10_localisation")
        d = pd.read_csv(p); fig, ax = plt.subplots(figsize=(5, 3))
        ax.bar(d.method, d.iou_ge_0_5, color=OI[0]); ax2 = ax.twinx(); ax2.plot(d.method, d.latency_ms_median, "o-", color=OI[1])
        ax.set_ylabel("fraction IoU >= 0.5"); ax2.set_ylabel("median latency (ms)", color=OI[1]); ax2.spines["right"].set_visible(True)
        fig.tight_layout(); fig.savefig(os.path.join(F, "fig_localisation.png")); plt.close(fig)
    p = os.path.join(R, "latency_stages.csv")
    if os.path.exists(p):
        st = pd.read_csv(p, index_col=0)
        keep = [i for i in st.index if i.endswith("_ms") and i != "total_ms"]
        save_table(st.reset_index().rename(columns={"index": "stage"}), "T11_latency_stages")
        fig, ax = plt.subplots(figsize=(7, 3)); s = st.loc[keep, "median_ms"].sort_values()
        ax.barh(s.index, s.values, color=OI[0]); ax.set_xlabel("median ms / image (sandbox CPU, not a Pi)")
        fig.tight_layout(); fig.savefig(os.path.join(F, "fig_latency.png")); plt.close(fig)
    p = os.path.join(R, "system_metrics.json")
    if os.path.exists(p):
        sm = json.load(open(p))
        rows = [dict(item=f"peak RSS: {k}", value_mb=v["peak_mb"]) for k, v in sm["memory"].items()]
        rows += [dict(item=f"size: {k}", value_mb=v) for k, v in sm["sizes_mb"].items()]
        save_table(pd.DataFrame(rows), "T12_memory_and_sizes")


def fig_guidance():
    p = os.path.join(R, "guidance_results.json")
    if os.path.exists(p):
        g = json.load(open(p)); save_table(pd.DataFrame([{k: v for k, v in g.items() if k != "cause_distribution"}]), "T13_guidance")


if __name__ == "__main__":
    man, raw, df, dep, primary, secondary = load_all()
    t_dataset(man); fig_examples(man); t_ocr(raw, man, df, primary); t_ablation(man); t_sweeps(dep, primary, secondary)
    fig_confusion(); fig_rejection(); t_loso(); t_loc_sys(); fig_guidance()
    print("assets written:", sorted(os.listdir(T))[:50], sorted(os.listdir(F)))
