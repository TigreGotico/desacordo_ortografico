#!/usr/bin/env python3
"""Render the benchmark results (results.json) as PNG charts under benchmark/plots/."""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PLOTS = os.path.join(HERE, "plots")
NORMS = ["etymological", "pt_1973", "ao1990-pt", "br_1971", "ao1990-br"]

INK = "#1b1b2b"
ACCENT = "#3563E9"
ACCENT2 = "#E9683C"
GOOD = "#2BA84A"


def _load():
    with open(os.path.join(HERE, "results.json"), encoding="utf-8") as f:
        return json.load(f)


def _bar_color(v):
    return GOOD if v >= 0.9 else (ACCENT if v >= 0.75 else ACCENT2)


def plot_by_pair(res):
    pairs = res["conversion"]["by_pair"]
    labels = list(pairs)
    exact = [pairs[p]["exact"] / pairs[p]["n"] for p in labels]
    token = [pairs[p]["token_acc"] for p in labels]
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(y + 0.2, token, height=0.38, color="#C7D2FE", label="token accuracy")
    ax.barh(y - 0.2, exact, height=0.38, color=ACCENT, label="exact-match")
    for i, (e, t) in enumerate(zip(exact, token)):
        ax.text(e + 0.01, i - 0.2, f"{e:.0%}", va="center", fontsize=8, color=INK)
        ax.text(t + 0.01, i + 0.2, f"{t:.0%}", va="center", fontsize=8, color="#555")
    ax.set_yticks(y)
    ax.set_yticklabels([l.replace("->", " → ") for l in labels], fontsize=9)
    ax.set_xlim(0, 1.08)
    ax.set_xlabel("accuracy")
    ax.set_title("Conversion accuracy by norm pair", fontweight="bold", color=INK)
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "conversion_by_pair.png"), dpi=150)
    plt.close(fig)


def plot_by_feature(res):
    bf = res["conversion"]["by_feature"]
    bn = res["conversion"]["by_feature_n"]
    items = sorted(bf.items(), key=lambda kv: kv[1])
    labels = [f"{k}  (n={bn[k]})" for k, _ in items]
    vals = [v for _, v in items]
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.barh(y, vals, color=[_bar_color(v) for v in vals])
    for i, v in enumerate(vals):
        ax.text(v + 0.01, i, f"{v:.0%}", va="center", fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlim(0, 1.08)
    ax.set_xlabel("sentence-level exact-match (conversions involving this feature)")
    ax.set_title("Conversion accuracy by orthographic feature", fontweight="bold", color=INK)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "conversion_by_feature.png"), dpi=150)
    plt.close(fig)


def plot_confusion(res):
    conf = res["detection"]["confusion"]
    preds = ["etymological", "pt_1973", "ao1990-pt", "br_1971", "ao1990-br",
             "ao1990", "not-portuguese"]
    M = np.array([[conf.get(r, {}).get(p, 0) for p in preds] for r in NORMS], dtype=float)
    Mn = M / M.sum(axis=1, keepdims=True).clip(min=1)
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    im = ax.imshow(Mn, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(preds)))
    ax.set_xticklabels(preds, rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(len(NORMS)))
    ax.set_yticklabels(NORMS, fontsize=9)
    for i in range(len(NORMS)):
        for j in range(len(preds)):
            if M[i, j]:
                ax.text(j, i, int(M[i, j]), ha="center", va="center", fontsize=7,
                        color="white" if Mn[i, j] > 0.5 else INK)
    ax.set_xlabel("predicted")
    ax.set_ylabel("nominal norm")
    ax.set_title("Detection confusion (row-normalised colour, raw counts)\n"
                 "off-diagonal mostly = norms spelled identically for that sentence",
                 fontweight="bold", color=INK, fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="row fraction")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "detection_confusion.png"), dpi=150)
    plt.close(fig)


def plot_summary(res):
    c, d, g = res["conversion"], res["detection"], res["guard"]
    metrics = [
        ("conversion\nexact-match", c["overall_exact"]),
        ("conversion\ntoken-acc", c["overall_token"]),
        ("detection\ncompatible", d["compatible_acc"]),
        ("guard\naccuracy", g["acc"]),
    ]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    x = np.arange(len(metrics))
    vals = [v for _, v in metrics]
    ax.bar(x, vals, color=[_bar_color(v) for v in vals], width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.02, f"{v:.1%}", ha="center", fontsize=11, fontweight="bold", color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([m for m, _ in metrics], fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("accuracy")
    ax.set_title(f"desacordo_ortografico benchmark — {res['n']} parallel sentences "
                 f"({res['n'] * 5} renderings)", fontweight="bold", color=INK, fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "summary.png"), dpi=150)
    plt.close(fig)


def main():
    os.makedirs(PLOTS, exist_ok=True)
    res = _load()
    plot_summary(res)
    plot_by_pair(res)
    plot_by_feature(res)
    plot_confusion(res)
    print(f"wrote 4 charts to {PLOTS}/")


if __name__ == "__main__":
    main()
