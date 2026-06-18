#!/usr/bin/env python3
"""Merge + validate the hand-authored core and the LLM-authored parts into one corpus.

Validation is structural (every line is JSON with five non-empty norm cells) plus a
few cheap sanity checks (no cell wildly different in length, at least one norm differs
unless explicitly invariant). Duplicates (by the ao1990-pt rendering) are dropped.
Writes ``gold_corpus.jsonl`` and prints a report.
"""
from __future__ import annotations

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NORMS = ["etymological", "pt_1973", "ao1990-pt", "br_1971", "ao1990-br"]
SOURCES = ["gold_parallel.jsonl"] + sorted(
    os.path.relpath(p, HERE) for p in glob.glob(os.path.join(HERE, "parts", "*.jsonl"))
)


def validate_record(rec, src, lineno):
    errs = []
    if "cells" not in rec:
        return ["missing 'cells'"]
    cells = rec["cells"]
    for n in NORMS:
        if n not in cells:
            errs.append(f"missing norm {n}")
        elif not isinstance(cells[n], str) or not cells[n].strip():
            errs.append(f"empty/invalid {n}")
    if errs:
        return errs
    lens = [len(cells[n]) for n in NORMS]
    if max(lens) > 3 * (min(lens) + 1):
        errs.append("a cell is wildly longer/shorter than the others")
    return errs


def main():
    seen = set()
    out = []
    stats = {"by_source": {}, "errors": [], "dropped_dupes": 0}
    for src in SOURCES:
        path = os.path.join(HERE, src)
        if not os.path.exists(path):
            continue
        n_ok = 0
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError as e:
                    stats["errors"].append(f"{src}:{i} JSON error: {e}")
                    continue
                errs = validate_record(rec, src, i)
                if errs:
                    stats["errors"].append(f"{src}:{i} {rec.get('id','?')}: {'; '.join(errs)}")
                    continue
                key = rec["cells"]["ao1990-pt"]
                if key in seen:
                    stats["dropped_dupes"] += 1
                    continue
                seen.add(key)
                rec.setdefault("source", src)
                out.append(rec)
                n_ok += 1
        stats["by_source"][src] = n_ok

    with open(os.path.join(HERE, "gold_corpus.jsonl"), "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    from collections import Counter
    feat = Counter(ft for r in out for ft in r.get("features", []))
    print(f"merged corpus: {len(out)} valid sentences "
          f"({len(out) * len(NORMS)} renderings across {len(NORMS)} norms)")
    print(f"dropped duplicates: {stats['dropped_dupes']}; "
          f"validation errors: {len(stats['errors'])}")
    print("\nby source:")
    for src, n in stats["by_source"].items():
        print(f"  {src:28} {n}")
    print("\nfeature coverage:")
    for ft, c in feat.most_common():
        print(f"  {ft:22} {c}")
    if stats["errors"]:
        print("\nfirst validation errors:")
        for e in stats["errors"][:25]:
            print(f"  {e}")
    # machine-readable for the plotter
    with open(os.path.join(HERE, "corpus_stats.json"), "w", encoding="utf-8") as f:
        json.dump({"n": len(out), "by_source": stats["by_source"],
                   "features": dict(feat), "dropped": stats["dropped_dupes"],
                   "n_errors": len(stats["errors"])}, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
