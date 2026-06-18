"""Zero-dependency learned orthography classifier (NB + averaged perceptron).

Mirrors the design used in ``bifonia``: a Naive-Bayes model and an averaged-perceptron
model share **one JSON shape and one scoring rule** — a sparse dot product

    score[class] = bias[class] + Σ_f feats[f] · weights[class][f]

and the prediction is the argmax. For NB the weights are per-class log-likelihoods and
the bias is the log-prior; for the perceptron they are learned. Either way inference is
plain dict arithmetic — only ``json`` + stdlib, safe under the single-dependency
install. The detector uses **margin-based routing**: trust the model when the top-two
score margin clears a threshold, otherwise defer to the rule detector.
"""
from __future__ import annotations

import json
import math
import os
import random
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

_WORD = re.compile(r"[0-9A-Za-zÀ-ɏ]+")


def features(text: str, lo: int = 2, hi: int = 4) -> Dict[str, int]:
    """Character n-gram features (count dict) over boundary-padded words."""
    feats: Dict[str, int] = defaultdict(int)
    for tok in _WORD.findall(text.lower()):
        s = "^" + tok + "$"
        for n in range(lo, hi + 1):
            for i in range(len(s) - n + 1):
                feats[s[i : i + n]] += 1
    return feats


class LinearModel:
    """A loaded linear classifier (NB or averaged perceptron); shared scoring rule."""

    def __init__(self, model_type, classes, bias, weights, lo=2, hi=4, default_ll=None):
        self.model_type = model_type
        self.classes = classes
        self.bias = bias
        self.weights = weights          # {class: {feat: w}}
        self.lo, self.hi = lo, hi
        self.default_ll = default_ll or {}  # NB only: log P(unseen|class)

    # ----------------------------------------------------------------- scoring
    def scores(self, text: str) -> Dict[str, float]:
        feats = features(text, self.lo, self.hi)
        out = {}
        for c in self.classes:
            w = self.weights.get(c, {})
            s = self.bias.get(c, 0.0)
            dflt = self.default_ll.get(c, 0.0)
            for f, v in feats.items():
                wf = w.get(f)
                s += v * (wf if wf is not None else dflt)
            out[c] = s
        return out

    def predict(self, text: str) -> Optional[str]:
        if not self.classes:
            return None
        sc = self.scores(text)
        return max(sorted(sc), key=lambda c: sc[c])  # deterministic tie-break

    def predict_with_margin(self, text: str) -> Tuple[Optional[str], float]:
        if not self.classes:
            return None, 0.0
        ranked = sorted(self.scores(text).values(), reverse=True)
        pred = self.predict(text)
        margin = ranked[0] - ranked[1] if len(ranked) > 1 else float("inf")
        return pred, margin

    # ------------------------------------------------------------ serialisation
    def to_dict(self) -> dict:
        return {
            "version": 1, "model_type": self.model_type,
            "config": {"lo": self.lo, "hi": self.hi},
            "classes": self.classes, "bias": self.bias,
            "weights": self.weights, "default_ll": self.default_ll,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LinearModel":
        cfg = d.get("config", {})
        return cls(d["model_type"], d["classes"], d["bias"], d["weights"],
                   cfg.get("lo", 2), cfg.get("hi", 4), d.get("default_ll"))

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "LinearModel":
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


# ----------------------------------------------------------------- training
def train_naive_bayes(texts: List[str], labels: List[str], lo=2, hi=4) -> LinearModel:
    counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    totals: Dict[str, int] = defaultdict(int)
    docs: Dict[str, int] = defaultdict(int)
    vocab = set()
    for text, label in zip(texts, labels):
        docs[label] += 1
        for f, v in features(text, lo, hi).items():
            counts[label][f] += v
            totals[label] += v
            vocab.add(f)
    classes = sorted(docs)
    n = sum(docs.values())
    vlen = len(vocab)
    bias, weights, default_ll = {}, {}, {}
    for c in classes:
        bias[c] = math.log(docs[c] / n)
        denom = totals[c] + vlen
        weights[c] = {f: math.log((counts[c][f] + 1) / denom) for f in vocab}
        default_ll[c] = math.log(1 / denom)
    return LinearModel("nb", classes, bias, weights, lo, hi, default_ll)


def train_perceptron_averaged(texts, labels, lo=2, hi=4, epochs=12, seed=0) -> LinearModel:
    """Multiclass averaged perceptron with lazy weight averaging (Daumé trick)."""
    classes = sorted(set(labels))
    feats = [features(t, lo, hi) for t in texts]
    w = {c: defaultdict(float) for c in classes}
    b = {c: 0.0 for c in classes}
    tw = {c: defaultdict(float) for c in classes}     # cumulative weights
    tb = {c: 0.0 for c in classes}
    tw_t = {c: defaultdict(int) for c in classes}      # last-touch timestamps
    tb_t = {c: 0 for c in classes}
    rng = random.Random(seed)
    order = list(range(len(texts)))
    step = 1
    for _ in range(epochs):
        rng.shuffle(order)
        for idx in order:
            fs, gold = feats[idx], labels[idx]
            sc = {}
            for c in classes:
                s = b[c]
                wc = w[c]
                for f, v in fs.items():
                    s += v * wc[f]
                sc[c] = s
            pred = max(sorted(classes), key=lambda c: sc[c])
            if pred != gold:
                for c, sign in ((gold, 1.0), (pred, -1.0)):
                    tb[c] += (step - tb_t[c]) * b[c]
                    tb_t[c] = step
                    b[c] += sign
                    wc, twc, tsc = w[c], tw[c], tw_t[c]
                    for f, v in fs.items():
                        twc[f] += (step - tsc[f]) * wc[f]
                        tsc[f] = step
                        wc[f] += sign * v
            step += 1
    bias, weights = {}, {}
    for c in classes:
        tb[c] += (step - tb_t[c]) * b[c]
        bias[c] = tb[c] / step
        twc, tsc, wc = tw[c], tw_t[c], w[c]
        wf = {}
        for f, val in wc.items():
            twc[f] += (step - tsc[f]) * val
            avg = twc[f] / step
            if abs(avg) > 1e-9:
                wf[f] = avg
        weights[c] = wf
    return LinearModel("perceptron_averaged", classes, bias, weights, lo, hi)


# ---------------------------------------------------------------- shipped models
# Two models ship (as in bifonia): Naive Bayes (the default; marginally more accurate
# here) and the averaged perceptron. Both share the LinearModel scoring rule.
_DATA = os.path.join(os.path.dirname(__file__), "data")
_PATHS = {"nb": os.path.join(_DATA, "detector_nb.json"),
          "perceptron": os.path.join(_DATA, "detector_perceptron.json")}
_CACHE: Dict[str, Optional[LinearModel]] = {}


def get_detector_model(kind: str = "nb") -> Optional[LinearModel]:
    """The shipped learned orthography model (``"nb"`` or ``"perceptron"``)."""
    if kind not in _CACHE:
        path = _PATHS.get(kind)
        model = None
        if path and os.path.exists(path):
            try:
                model = LinearModel.load(path)
            except Exception:  # pragma: no cover
                model = None
        _CACHE[kind] = model
    return _CACHE[kind]
