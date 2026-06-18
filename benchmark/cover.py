#!/usr/bin/env python3
"""Carrier-fill: guarantee every coverable AO1990-changed word appears at least once.

For each word still missing from the corpus, emit a short carrier sentence with the word
as a quoted term (POS-agnostic, grammatical, all other words invariant), derive its five
norms, and write them tagged ``source: coverage``. The quoted word is the only cell that
changes, so the sentence exercises exactly that word's orthographic change.
"""
from __future__ import annotations

import json
import os

from derive import build_maps, derive
from derive_corpus import infer_features

HERE = os.path.dirname(os.path.abspath(__file__))
_FRAMES = [
    "A palavra «{w}» foi escrita aqui.",
    "Reparei na palavra «{w}» ao ler.",
    "Sublinhei a palavra «{w}» no texto.",
    "Encontrei a palavra «{w}» na lista.",
    "Citei a palavra «{w}» de memória.",
]


def main():
    M = build_maps()
    words = [w.strip() for w in open(os.path.join(HERE, "coverage", "still_missing.txt"),
                                     encoding="utf-8") if w.strip()]
    out, failed = [], []
    for i, w in enumerate(words):
        d = derive(_FRAMES[i % len(_FRAMES)].format(w=w), M)
        if d is None:
            failed.append(w)
            continue
        out.append({"id": f"c{len(out):05d}", "features": infer_features(d, M),
                    "cells": d, "source": "coverage"})
    with open(os.path.join(HERE, "gold_coverage.jsonl"), "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"carrier rows: {len(out)}; could not carry: {len(failed)}")
    if failed:
        print("  failed:", failed[:20])


if __name__ == "__main__":
    main()
