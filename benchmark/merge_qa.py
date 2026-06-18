#!/usr/bin/env python3
"""Apply the LLM QA corrections (benchmark/qa/out/*.jsonl) to the gold corpus.

Each correction line is {"id", "verdict":"fix"|"drop", ...}. A "fix" replaces the cells
and/or features; a "drop" removes the sentence. After applying, a final structural check
re-confirms the European and Brazilian lines are internally consistent (a correction that
introduced an inconsistency is dropped). Sister-sample corrections are applied too.
"""
from __future__ import annotations

import glob
import json
import os

from clean_gold import cells_consistent  # noqa: E402  (same dir)

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(path):
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def apply_parallel():
    rows = _load(os.path.join(HERE, "gold_corpus.jsonl"))
    order = [r["id"] for r in rows]
    by_id = {r["id"]: r for r in rows}
    fixes = drops = 0
    for qf in sorted(glob.glob(os.path.join(HERE, "qa", "out", "qa_*.jsonl"))):
        if qf.endswith("qa_sisters.jsonl"):
            continue
        for c in _load(qf):
            r = by_id.get(c["id"])
            if r is None:
                continue
            if c["verdict"] == "drop":
                by_id.pop(c["id"], None)
                drops += 1
            elif c["verdict"] == "fix":
                if "cells" in c:
                    r["cells"] = c["cells"]
                if "features" in c:
                    r["features"] = c["features"]
                fixes += 1

    out, struct_drop = [], 0
    for cid in order:
        r = by_id.get(cid)
        if r is None:
            continue
        if (cells_consistent(r, ["pt_1973", "ao1990-pt"])
                and cells_consistent(r, ["br_1971", "ao1990-br"])):
            out.append(r)
        else:
            struct_drop += 1
    with open(os.path.join(HERE, "gold_corpus.jsonl"), "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"parallel: applied {fixes} fixes, {drops} drops; "
          f"{struct_drop} dropped on post-merge inconsistency; final {len(out)} sentences")


def apply_sisters():
    path = os.path.join(HERE, "qa", "out", "qa_sisters.jsonl")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        print("sisters: no corrections")
        return
    rows = _load(os.path.join(HERE, "gold_sisters.jsonl"))
    by_id = {r["id"]: r for r in rows}
    fixes = drops = 0
    for c in _load(path):
        if c["verdict"] == "drop":
            by_id.pop(c["id"], None)
            drops += 1
        elif c["verdict"] == "fix":
            by_id[c["id"]]["text"] = c["text"]
            fixes += 1
    out = [r for r in rows if r["id"] in by_id]
    with open(os.path.join(HERE, "gold_sisters.jsonl"), "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"sisters: applied {fixes} fixes, {drops} drops; final {len(out)}")


if __name__ == "__main__":
    apply_parallel()
    apply_sisters()
