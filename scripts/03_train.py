"""Select OCR configuration, train readability classifier + calibrated rejectors, evaluate on the held-out test
split. All model selection uses development data (train+val, grouped by item). The test split is touched once."""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.base import clone

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hallmark import ROOT, CFG  # noqa: E402
from hallmark import metrics as M  # noqa: E402
from hallmark import models as MD  # noqa: E402

R = os.path.join(ROOT, "results")
LABELS = ["readable", "partial", "unreadable"]
CONFIGS = [(e, v) for e in ("tesseract", "rapidocr") for v in ("raw", "red", "enh", "bin")]


def load():
    man = pd.read_csv(os.path.join(ROOT, "data", "manifest.csv"))
    raw = pd.read_csv(os.path.join(R, "ocr_raw.csv"))
    return man, raw


def select_ocr(man, raw):
    df = man.merge(raw, on="image_id")
    dev = df[df.split.isin(["train", "val"])]
    rows = []
    for e, v in CONFIGS:
        preds = dev[f"{e}_{v}_text"].fillna("").tolist()
        s = M.ocr_summary(dev["text"].tolist(), preds)
        rows.append(dict(engine=e, variant=v, **s))
    tab = pd.DataFrame(rows).sort_values(["exact", "CER"], ascending=[False, True])
    best = tab.iloc[0]
    primary = (best.engine, best.variant)
    other = tab[tab.engine != best.engine].iloc[0]
    secondary = (other.engine, other.variant)
    tab.to_csv(os.path.join(R, "ocr_config_selection_dev.csv"), index=False)
    return primary, secondary, tab


def readability_experiment(df, dev, test, groups):
    out = {}
    for fs_name in ("quality_only", "quality+ocr_unc"):
        feats = MD.FEATURE_SETS[fs_name]
        X, y = dev[feats].values.astype(float), dev["readability"].values
        res = []
        for name, mdl in MD.readability_zoo().items():
            f1s, accs = [], []
            for tr, te in GroupKFold(5).split(X, y, groups):
                m = clone(mdl).fit(X[tr], y[tr]); p = m.predict(X[te])
                s = M.clf_summary(y[te], p, LABELS)
                f1s.append(s["f1_macro"]); accs.append(s["accuracy"])
            res.append(dict(feature_set=fs_name, model=name, cv_f1_mean=np.mean(f1s), cv_f1_sd=np.std(f1s),
                            cv_acc_mean=np.mean(accs)))
        cv = pd.DataFrame(res).sort_values("cv_f1_mean", ascending=False)
        best = cv.iloc[0].model
        m = clone(MD.readability_zoo()[best]).fit(X, y)
        pred = m.predict(test[feats].values.astype(float))
        # also evaluate every model on test for the comparison table (selection was by CV only)
        allt = {}
        for name, mdl in MD.readability_zoo().items():
            mm = clone(mdl).fit(X, y)
            allt[name] = M.clf_summary(test["readability"].values, mm.predict(test[feats].values.astype(float)), LABELS)
        out[fs_name] = dict(cv=cv.to_dict("records"), selected=best, test=M.clf_summary(test["readability"].values, pred, LABELS),
                            test_all_models={k: {kk: vv for kk, vv in v.items() if kk in ("accuracy", "precision_macro", "recall_macro", "f1_macro")}
                                             for k, v in allt.items()})
        if fs_name == "quality_only":
            MD.save(dict(model=m, features=feats, labels=LABELS, name=best), os.path.join(ROOT, "models", "readability.joblib"))
    return out


def rule_gate_params(dev):
    clean = dev[dev.condition == "clean"]
    return dict(lap_min=float(clean["r_lapvar_log"].quantile(0.05)), sat_max=float(max(clean["r_sat_frac"].quantile(0.95), 0.01)),
                bright_lo=float(clean["f_bright"].quantile(0.05)), bright_hi=float(clean["f_bright"].quantile(0.95)),
                contrast_min=float(clean["r_contrast"].quantile(0.05)))


def gate_pass(d, g):
    return ((d["r_lapvar_log"] >= g["lap_min"]) & (d["r_sat_frac"] <= g["sat_max"]) & (d["f_bright"] >= g["bright_lo"])
            & (d["f_bright"] <= g["bright_hi"]) & (d["r_contrast"] >= g["contrast_min"])).values


def rejection_experiment(dev, test, gdev, gtest):
    y_dev = dev["correct"].values.astype(int); y_te = test["correct"].values.astype(int)
    targets = CFG["rejection"]["target_risks"]
    strategies = {}
    # --- S0 accept all
    strategies["S0 accept-all"] = dict(score_te=np.ones(len(test)), score_dev=np.ones(len(dev)), prob=False)
    # --- S1 raw OCR confidence (uncalibrated)
    strategies["S1 OCR conf (raw)"] = dict(score_te=test["p_conf"].values, score_dev=dev["p_conf"].values, prob=True)
    # --- S2 conventional rule-based quality gate + raw OCR confidence
    g = rule_gate_params(dev)
    sg_dev = np.where(gate_pass(dev, g), dev["p_conf"].values, -1.0); sg_te = np.where(gate_pass(test, g), test["p_conf"].values, -1.0)
    strategies["S2 rule gate + OCR conf"] = dict(score_te=sg_te, score_dev=sg_dev, prob=False)
    # --- learned rejectors
    chosen = {}
    for name, fs in (("S3 OCR-uncertainty only (learned)", "ocr_unc_only"), ("S4 quality only (learned)", "quality_only"),
                     ("S5 quality + OCR-uncertainty", "quality+ocr_unc"), ("S6 + grammar validity (ablation)", "quality+ocr_unc+grammar")):
        feats = MD.FEATURE_SETS[fs]
        best, bestA, rows = None, 9, []
        for mname, base in MD.rejector_zoo().items():
            rej = MD.CalibratedRejector(base, feats).fit(dev, y_dev, gdev, targets)
            a = M.aurc(rej.oof_raw, y_dev)
            rows.append(dict(strategy=name, model=mname, dev_oof_aurc=a))
            if a < bestA:
                best, bestA, bm = rej, a, mname
        chosen[name] = dict(model=bm, rej=best, dev_table=rows, fs=fs)
        strategies[name] = dict(score_te=best.score(test), score_dev=best.oof_cal, prob=True, rej=best)
    # --- evaluate
    res = {}
    for name, s in strategies.items():
        sc_te, sc_dev = np.asarray(s["score_te"], float), np.asarray(s["score_dev"], float)
        r = dict(aurc=M.aurc(sc_te, y_te), eaurc=M.eaurc(sc_te, y_te), full_coverage_error=float(1 - y_te.mean()))
        for cov in (0.5, 0.7, 0.9):
            r[f"risk_at_cov_{int(cov*100)}"] = M.risk_at_coverage(sc_te, y_te, cov)
        r["at_target"] = {}; r["at_target_ucb"] = {}
        for t in targets:
            tau = M.threshold_for_risk(sc_dev, y_dev, t)
            r["at_target"][str(t)] = dict(tau=tau, **M.selective_at(sc_te, y_te, tau))
            tau_u = M.threshold_for_risk_ucb(sc_dev, y_dev, t)
            r["at_target_ucb"][str(t)] = dict(tau=tau_u, **M.selective_at(sc_te, y_te, tau_u))
        if s["prob"]:
            r["ece"] = M.ece(np.clip(sc_te, 0, 1), y_te); r["brier"] = M.brier(np.clip(sc_te, 0, 1), y_te)
        res[name] = r
    # paired item-cluster bootstrap of AURC differences vs S1
    base = strategies["S1 OCR conf (raw)"]["score_te"]
    for name, s in strategies.items():
        if name in ("S0 accept-all", "S1 OCR conf (raw)"):
            continue
        d = lambda idx, a=s["score_te"]: M.aurc(np.asarray(a)[idx], y_te[idx]) - M.aurc(np.asarray(base)[idx], y_te[idx])
        m, lo, hi = M.cluster_bootstrap(test["item_id"].values, d, n=CFG["rejection"]["bootstrap_resamples"], seed=1)
        res[name]["delta_aurc_vs_S1"] = dict(mean=m, ci_lo=lo, ci_hi=hi)
        a = lambda idx, x=s["score_te"]: M.aurc(np.asarray(x)[idx], y_te[idx])
        m2, lo2, hi2 = M.cluster_bootstrap(test["item_id"].values, a, n=CFG["rejection"]["bootstrap_resamples"], seed=2)
        res[name]["aurc_ci"] = dict(mean=m2, ci_lo=lo2, ci_hi=hi2)
    # paired comparisons that isolate what each signal adds
    pair = {}
    for a_, b_ in (("S5 quality + OCR-uncertainty", "S3 OCR-uncertainty only (learned)"), ("S4 quality only (learned)", "S1 OCR conf (raw)"),
                   ("S3 OCR-uncertainty only (learned)", "S1 OCR conf (raw)"), ("S5 quality + OCR-uncertainty", "S4 quality only (learned)")):
        fa, fb = strategies[a_]["score_te"], strategies[b_]["score_te"]
        d = lambda idx, fa=fa, fb=fb: M.aurc(np.asarray(fa)[idx], y_te[idx]) - M.aurc(np.asarray(fb)[idx], y_te[idx])
        m, lo, hi = M.cluster_bootstrap(test["item_id"].values, d, n=CFG["rejection"]["bootstrap_resamples"], seed=5)
        pair[f"{a_}  minus  {b_}"] = dict(mean=m, ci_lo=lo, ci_hi=hi)
    res["_paired_delta_aurc"] = pair
    a1 = lambda idx: M.aurc(np.asarray(base)[idx], y_te[idx])
    m, lo, hi = M.cluster_bootstrap(test["item_id"].values, a1, n=CFG["rejection"]["bootstrap_resamples"], seed=2)
    res["S1 OCR conf (raw)"]["aurc_ci"] = dict(mean=m, ci_lo=lo, ci_hi=hi)
    return res, strategies, chosen, g


def main():
    os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)
    man, raw = load()
    primary, secondary, tab = select_ocr(man, raw)
    print("OCR selection (dev):\n", tab.round(3).to_string(index=False))
    print("primary", primary, "secondary", secondary)
    df = MD.assemble(raw, man, primary, secondary)
    dev = df[df.split.isin(["train", "val"])].reset_index(drop=True)
    test = df[df.split == "test"].reset_index(drop=True)
    gdev = dev["item_id"].values
    print("dev", len(dev), "test", len(test), "| dev OCR exact", dev.correct.mean().round(3), "test exact", test.correct.mean().round(3))

    rd = readability_experiment(df, dev, test, gdev)
    json.dump(rd, open(os.path.join(R, "readability_results.json"), "w"), indent=1)
    for k, v in rd.items():
        print(k, "selected", v["selected"], "test acc/F1", round(v["test"]["accuracy"], 3), round(v["test"]["f1_macro"], 3))

    rj, strategies, chosen, gate = rejection_experiment(dev, test, gdev, test["item_id"].values)
    json.dump(dict(results=rj, gate=gate, chosen={k: dict(model=v["model"], dev_table=v["dev_table"]) for k, v in chosen.items()},
                   primary=primary, secondary=secondary), open(os.path.join(R, "rejection_results.json"), "w"), indent=1, default=float)
    for k, v in rj.items():
        if k.startswith("_"):
            continue
        print(f"{k:38s} AURC {v['aurc']:.4f}  risk@70% {v['risk_at_cov_70']:.3f}  @5%: cov {v['at_target']['0.05']['coverage']:.2f} "
              f"err {v['at_target']['0.05']['accepted_error_rate']:.3f}")
    # test score table for plotting
    out = test[["image_id", "item_id", "source", "condition", "readability", "correct", "cer", "text", "pred_text"]].copy()
    for k, s in strategies.items():
        out["score_" + k.split()[0]] = np.asarray(s["score_te"], float)
    out.to_csv(os.path.join(R, "test_scores.csv"), index=False)
    dev_out = dev[["image_id", "item_id", "correct"]].copy()
    for k, s in strategies.items():
        dev_out["score_" + k.split()[0]] = np.asarray(s["score_dev"], float)
    dev_out.to_csv(os.path.join(R, "dev_scores.csv"), index=False)

    # --- deployed artifacts
    rej = chosen["S5 quality + OCR-uncertainty"]["rej"]
    guid = MD.Guidance().fit(dev)
    MD.save(dict(rejector=rej, primary=primary, secondary=secondary, taus=rej.taus, taus_ucb=rej.taus_ucb, features=rej.features,
                 name=chosen["S5 quality + OCR-uncertainty"]["model"]), os.path.join(ROOT, "models", "rejector.joblib"))
    MD.save(guid, os.path.join(ROOT, "models", "guidance.joblib"))
    json.dump(dict(primary=primary, secondary=secondary, taus=rej.taus, taus_ucb=rej.taus_ucb, rejector=chosen["S5 quality + OCR-uncertainty"]["model"],
                   readability=rd["quality_only"]["selected"]), open(os.path.join(ROOT, "models", "deployment.json"), "w"), indent=1)

    # --- recapture-guidance evaluation (top-1 cause vs manifest quality labels)
    tau = rej.taus_ucb["0.05"] if np.isfinite(rej.taus_ucb["0.05"]) else rej.taus["0.05"]
    s_te = rej.score(test); rej_mask = s_te < tau
    qcols = ["q_blur", "q_glare", "q_resolution", "q_contrast", "q_lighting", "q_occlusion", "q_viewing"]
    hit, n, base_hit = 0, 0, 0
    causes = []
    rng = np.random.default_rng(0)
    for i in np.nonzero(rej_mask)[0]:
        row = test.iloc[i]
        poor = {c for c in qcols if row[c] != "good"}
        if not poor:
            continue
        cause, _, _ = guid.diagnose(row)
        n += 1
        hit += any(c in poor for c in MD.CAUSE_TO_LABELS[cause])
        rc = rng.choice(list(MD.CAUSE_TO_LABELS))
        base_hit += any(c in poor for c in MD.CAUSE_TO_LABELS[rc])
        causes.append(cause)
    gres = dict(n_rejected_with_flagged_factor=n, top1_hit_rate=hit / max(n, 1), random_cause_hit_rate=base_hit / max(n, 1),
                n_rejected_total=int(rej_mask.sum()), n_rejected_no_flagged_factor=int(rej_mask.sum()) - n,
                cause_distribution=pd.Series(causes).value_counts().to_dict())
    json.dump(gres, open(os.path.join(R, "guidance_results.json"), "w"), indent=1)
    print("guidance", gres)


if __name__ == "__main__":
    main()
