#!/usr/bin/env python3
"""Derive a parallel corpus from generated modern sentences (gen/out/*.txt).

Reads one modern European-Portuguese sentence per line, derives all five norms with the
verified engine (derive.py), drops the uncoverable ones, infers the feature labels from
the cell differences, de-duplicates, and writes gold_generated.jsonl.
"""
from __future__ import annotations

import glob
import json
import os
import re

from derive import _TOK, build_maps, derive

HERE = os.path.dirname(os.path.abspath(__file__))
_CP = (("cç", "silent-ct"), ("ct", "silent-ct"), ("pç", "silent-pt"), ("pt", "silent-pt"),
       ("pc", "silent-pt"))


def infer_features(d, M):
    f = set()
    cell = {k: _TOK.findall(v) for k, v in d.items()}
    et, pt, ao = cell["etymological"], cell["pt_1973"], cell["ao1990-pt"]
    brm, br = cell["br_1971"], cell["ao1990-br"]
    # European line: etym vs pt_1973 (digraph/geminate/mn) and pt_1973 vs ao1990-pt (silent c/p)
    if len(et) == len(pt) == len(ao):
        for e, p, a in zip(et, pt, ao):
            el, pl, al = e.lower(), p.lower(), a.lower()
            if "ph" in el and "ph" not in pl:
                f.add("digraph-ph")
            if "th" in el and "th" not in pl:
                f.add("digraph-th")
            if re.search(r"[a-zà-ÿ]y", el) and "y" not in pl:
                f.add("digraph-y")
            if re.search(r"(ll|nn|mm|pp|tt|bb|gg|dd|ff|cc)", el) and not re.search(
                    r"(ll|nn|mm|pp|tt|bb|gg|dd|ff|cc)", pl):
                f.add("geminate")
            if ("mn" in el and "mn" not in pl) or ("ps" in el and "ps" not in pl):
                f.add("mn-cluster")
            if "ch" in el and "ch" not in pl:
                f.add("ch-k")
            for cl, name in _CP:
                if cl in pl and cl not in al:
                    f.add(name)
            if "-" in pl and "-" not in al:
                f.add("hyphen-rs")
    # Brazilian: nasal / dual / divergence (ao1990-pt vs ao1990-br) and trema/diphthong
    if len(ao) == len(br):
        for a, b in zip(ao, br):
            al, bl = a.lower(), b.lower()
            if al != bl:
                if al in M.lex.dual_pt2br:
                    f.add("dual-facto")
                elif al in M.lex.divergence_pt2br:
                    f.add("divergence")
                else:
                    f.add("nasal-vowel")
    if "ü" in d["br_1971"].lower():
        f.add("trema")
    if len(br) == len(brm):
        for a, b in zip(br, brm):
            if a.lower() != b.lower() and "ü" not in b.lower():
                f.add("br-diphthong-accent")
    if re.search(r"\b(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|"
                 r"outubro|novembro|dezembro)\b", d["ao1990-pt"].lower()):
        f.add("months")
    return sorted(f)


def main():
    M = build_maps()
    seen = set()
    out = []
    n_in = rejected = 0
    sources = (sorted(glob.glob(os.path.join(HERE, "gen", "out", "*.txt")))
               + sorted(glob.glob(os.path.join(HERE, "coverage", "out", "*.txt"))))
    for path in sources:
        for line in open(path, encoding="utf-8"):
            s = line.strip().lstrip("-•0123456789. )").strip()
            if len(s) < 12 or not s[0].isalpha() and s[0] not in "OAEUaeiou":
                continue
            n_in += 1
            d = derive(s, M)
            if d is None:
                rejected += 1
                continue
            key = d["ao1990-pt"].lower()
            if key in seen:
                continue
            seen.add(key)
            out.append({"id": f"d{len(out):05d}", "features": infer_features(d, M),
                        "cells": d, "source": "derived"})
    with open(os.path.join(HERE, "gold_generated.jsonl"), "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    feat = Counter(ft for r in out for ft in r["features"])
    print(f"read {n_in} sentences; {rejected} rejected; {len(out)} unique derived")
    for ft, c in feat.most_common():
        print(f"  {ft:22} {c}")


if __name__ == "__main__":
    main()
