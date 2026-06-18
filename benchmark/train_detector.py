#!/usr/bin/env python3
"""Train + honestly evaluate the learned orthography detectors (NB + perceptron).

5-fold cross-validation split BY SENTENCE (all five renderings of a sentence stay in
one fold, so the model never sees a near-identical string at train and test time).
Compares the rule detector, Naive Bayes, the averaged perceptron, and a margin-routed
ensemble (model when confident, else rules). Ships the perceptron.

    python benchmark/train_detector.py
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict

from desacordo_ortografico.detect import detect
from desacordo_ortografico.guard import NotPortuguese
from desacordo_ortografico.ml import train_naive_bayes, train_perceptron_averaged

HERE = os.path.dirname(os.path.abspath(__file__))
NORMS = ["etymological", "pt_1973", "ao1990-pt", "br_1971", "ao1990-br"]
DATA = os.path.join(os.path.dirname(HERE), "desacordo_ortografico", "data")
TAU = 1.0  # perceptron margin below which the ensemble defers to the rule detector


def load_corpus():
    with open(os.path.join(HERE, "gold_corpus.jsonl"), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def rule_label(text):
    r = detect(text, method="rules")
    if isinstance(r, NotPortuguese):
        return "not-portuguese"
    eid = r.id
    if eid.startswith("pt_1973"):
        return "pt_1973"
    if eid.startswith("br_1971"):
        return "br_1971"
    return eid  # etymological, ao1990-pt, ao1990-br, ao1990


def compatible(pred, shared_cols):
    if pred == "ao1990":
        return bool({"ao1990-pt", "ao1990-br"} & shared_cols)
    return pred in shared_cols


def evaluate():
    corpus = load_corpus()
    folds = defaultdict(list)
    for i, s in enumerate(corpus):
        folds[i % 5].append(s)

    acc = {m: {"strict": 0, "compat": 0} for m in ("rules", "nb", "perceptron", "ensemble")}
    total = 0
    for k in range(5):
        train = [s for j in range(5) if j != k for s in folds[j]]
        test = folds[k]
        X = [s["cells"][c] for s in train for c in NORMS]
        y = [c for s in train for c in NORMS]
        nb = train_naive_bayes(X, y)
        pc = train_perceptron_averaged(X, y)
        for s in test:
            shared = defaultdict(set)
            for c in NORMS:
                shared[s["cells"][c]].add(c)
            for c in NORMS:
                text = s["cells"][c]
                total += 1
                sc = shared[text]
                p_rule = rule_label(text)
                p_nb = nb.predict(text)
                p_pc, margin = pc.predict_with_margin(text)
                p_ens = p_pc if margin >= TAU else p_rule
                for name, pred in (("rules", p_rule), ("nb", p_nb),
                                   ("perceptron", p_pc), ("ensemble", p_ens)):
                    acc[name]["strict"] += (pred == c)
                    acc[name]["compat"] += compatible(pred, sc)

    print(f"5-fold CV over {total} renderings (split by sentence):\n")
    print(f"  {'detector':12} {'strict':>9} {'compatible':>12}")
    for m in ("rules", "nb", "perceptron", "ensemble"):
        print(f"  {m:12} {acc[m]['strict']/total:>8.1%} {acc[m]['compat']/total:>11.1%}")
    return {m: {k: acc[m][k] / total for k in acc[m]} for m in acc} | {"n": total}


def train_full():
    corpus = load_corpus()
    X = [s["cells"][c] for s in corpus for c in NORMS]
    y = [c for s in corpus for c in NORMS]
    train_naive_bayes(X, y).save(os.path.join(DATA, "detector_nb.json"))
    train_perceptron_averaged(X, y).save(os.path.join(DATA, "detector_perceptron.json"))
    print(f"\ntrained NB + averaged perceptron on {len(X)} renderings -> {DATA}/")
    print("classes:", dict(Counter(y)))


if __name__ == "__main__":
    res = evaluate()
    with open(os.path.join(HERE, "detector_cv.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    train_full()
