"""OCR, classification and selective-prediction metrics (all implemented here and unit-tested)."""
import numpy as np
from rapidfuzz.distance import Levenshtein
from sklearn.metrics import (accuracy_score, confusion_matrix, precision_recall_fscore_support)


def _ns(s):
    return (s or "").replace(" ", "")


def cer(gt, pred):
    """Character error rate on whitespace-stripped strings: Levenshtein(gt, pred) / len(gt)."""
    g, p = _ns(gt), _ns(pred)
    return Levenshtein.distance(g, p) / max(len(g), 1)


def wer(gt, pred):
    g, p = gt.split(), pred.split()
    return Levenshtein.distance(g, p) / max(len(g), 1)


def exact(gt, pred):
    """Whitespace-insensitive exact transcription match (primary correctness definition)."""
    return float(_ns(gt) == _ns(pred))


def exact_strict(gt, pred):
    return float(" ".join(gt.split()) == " ".join(pred.split()))


def ocr_summary(gts, preds):
    gts, preds = list(gts), list(preds)
    return dict(CER=float(np.mean([cer(g, p) for g, p in zip(gts, preds)])),
                WER=float(np.mean([wer(g, p) for g, p in zip(gts, preds)])),
                exact=float(np.mean([exact(g, p) for g, p in zip(gts, preds)])),
                exact_strict=float(np.mean([exact_strict(g, p) for g, p in zip(gts, preds)])), n=len(gts))


def clf_summary(y, p, labels):
    pr, rc, f1, _ = precision_recall_fscore_support(y, p, labels=labels, average="macro", zero_division=0)
    ppc, rpc, fpc, spc = precision_recall_fscore_support(y, p, labels=labels, average=None, zero_division=0)
    return dict(accuracy=float(accuracy_score(y, p)), precision_macro=float(pr), recall_macro=float(rc), f1_macro=float(f1),
                per_class={l: dict(precision=float(a), recall=float(b), f1=float(c), support=int(d))
                           for l, a, b, c, d in zip(labels, ppc, rpc, fpc, spc)},
                confusion=confusion_matrix(y, p, labels=labels).tolist(), labels=list(labels))


# ---------------- selective prediction -----------------
def risk_coverage(score, correct):
    """Return coverage[], risk[] when accepting items in order of decreasing score (ties broken stably)."""
    score = np.asarray(score, float); err = 1.0 - np.asarray(correct, float)
    order = np.argsort(-score, kind="stable")
    e = err[order]
    n = len(e)
    cov = np.arange(1, n + 1) / n
    risk = np.cumsum(e) / np.arange(1, n + 1)
    return cov, risk


def aurc(score, correct):
    """Area under the risk-coverage curve (mean selective risk over coverages 1/n..1); lower is better."""
    _, risk = risk_coverage(score, correct)
    return float(risk.mean())


def eaurc(score, correct):
    """Excess AURC: AURC minus that of an oracle ranking (errors rejected first)."""
    c = np.asarray(correct, float)
    return aurc(score, correct) - aurc(c, correct)


def threshold_for_risk(score, correct, target):
    """Largest-coverage threshold tau (accept if score >= tau) with empirical selective risk <= target on the
    given (development) data. Returns +inf if no threshold satisfies it."""
    score = np.asarray(score, float); err = 1.0 - np.asarray(correct, float)
    best = np.inf
    for tau in np.unique(score)[::-1]:  # high -> low
        m = score >= tau
        if m.sum() and err[m].mean() <= target:
            best = tau
    return float(best)


def threshold_for_risk_ucb(score, correct, target, delta=0.1):
    """Risk-controlled threshold: the lowest tau (largest coverage) whose accepted-error rate has a one-sided
    Clopper-Pearson upper confidence bound (level 1-delta) <= target on the development data. More conservative than
    `threshold_for_risk`; motivated by the bound-based selective classifier of Geifman & El-Yaniv (2017).
    NOTE: items from one inscription are correlated, so the nominal level is approximate."""
    from scipy.stats import beta
    score = np.asarray(score, float); err = (1.0 - np.asarray(correct, float))
    best = np.inf
    for tau in np.unique(score)[::-1]:
        m = score >= tau
        n = int(m.sum()); k = int(err[m].sum())
        if n == 0:
            continue
        ub = 1.0 if k >= n else float(beta.ppf(1 - delta, k + 1, n - k))
        if ub <= target:
            best = tau
    return float(best)


def selective_at(score, correct, tau):
    score = np.asarray(score, float); c = np.asarray(correct, float)
    m = score >= tau
    cov = float(m.mean())
    risk = float(1.0 - c[m].mean()) if m.sum() else float("nan")
    n_acc_err = int(((1 - c)[m]).sum())
    return dict(coverage=cov, rejection_rate=1 - cov, accepted_error_rate=risk, accepted_errors=n_acc_err, accepted=int(m.sum()))


def coverage_at_risk_oracle(score, correct, target):
    """Best achievable coverage on THIS data with risk <= target (threshold chosen on the same data; an
    optimistic reference used for the risk-coverage plot, never for headline results)."""
    cov, risk = risk_coverage(score, correct)
    ok = np.nonzero(risk <= target)[0]
    return float(cov[ok.max()]) if len(ok) else 0.0


def risk_at_coverage(score, correct, coverage):
    cov, risk = risk_coverage(score, correct)
    i = int(np.searchsorted(cov, coverage - 1e-12))
    return float(risk[min(i, len(risk) - 1)])


def ece(prob, correct, bins=10):
    prob = np.asarray(prob, float); c = np.asarray(correct, float)
    edges = np.linspace(0, 1, bins + 1)
    tot = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (prob > lo) & (prob <= hi) if lo > 0 else (prob >= lo) & (prob <= hi)
        if m.sum():
            tot += m.mean() * abs(c[m].mean() - prob[m].mean())
    return float(tot)


def brier(prob, correct):
    return float(np.mean((np.asarray(prob, float) - np.asarray(correct, float)) ** 2))


def cluster_bootstrap(groups, stat_fn, n=1000, seed=0):
    """Bootstrap over groups (items): resample group ids with replacement, rebuild the index set."""
    rng = np.random.default_rng(seed)
    groups = np.asarray(groups)
    ug = np.unique(groups)
    idx_by = {g: np.nonzero(groups == g)[0] for g in ug}
    vals = []
    for _ in range(n):
        pick = rng.choice(ug, size=len(ug), replace=True)
        idx = np.concatenate([idx_by[g] for g in pick])
        vals.append(stat_fn(idx))
    vals = np.array(vals, float)
    return float(np.nanmean(vals)), float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))
