#!/usr/bin/env python3
"""Attribute benchmark failures: detection vs conversion, rule-limitation vs gold-error.

For every rule failure it classifies the cause from mechanical signals so we can say
where the library loses points and whether the fault is the library's or the corpus's.
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict

from desacordo_ortografico import OrthographyConverter, detect
from desacordo_ortografico.guard import NotPortuguese
from desacordo_ortografico.lexicon import deaccent, get_lexicon

HERE = os.path.dirname(os.path.abspath(__file__))
NORMS = ["etymological", "pt_1973", "ao1990-pt", "br_1971", "ao1990-br"]
PAIRS = [("etymological", "pt_1973"), ("etymological", "ao1990-pt"),
         ("etymological", "ao1990-br"), ("pt_1973", "ao1990-pt"),
         ("br_1971", "ao1990-br"), ("ao1990-pt", "ao1990-br"),
         ("ao1990-br", "ao1990-pt")]
_CP = ("cç", "ct", "pç", "pt")


def load():
    with open(os.path.join(HERE, "gold_corpus.jsonl"), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def decluster(w):
    for p, r in (("cç", "ç"), ("ct", "t"), ("pç", "ç"), ("pt", "t")):
        w = w.replace(p, r)
    return w


def classify_token(got, gold, lex):
    """Return (category, verdict) for a got/gold token mismatch."""
    g, h = got.lower(), gold.lower()
    if g == h:
        return "case/month", "rule-limitation"
    if deaccent(g) == deaccent(h):
        # same letters, differ only by accent
        if g == deaccent(g):          # we produced the bare form, gold is accented
            return "accent-not-restored", "rule-limitation"
        return "accent-mismatch", "gold-suspect"
    if decluster(g) == h or decluster(deaccent(g)) == deaccent(h):
        return "silent-cp-not-dropped", "rule-limitation"
    if decluster(h) == g:             # gold kept a cluster we dropped
        return "silent-cp-overkept", "gold-suspect"
    # different lemma entirely
    if h in lex.wordset and g in lex.wordset and deaccent(g)[:3] != deaccent(h)[:3]:
        return "different-word", "gold-suspect"
    return "other", "unclassified"


def conversion(corpus, conv, lex):
    fails = 0
    n = 0
    cats = Counter()
    verdicts = Counter()
    samples = defaultdict(list)
    for s in corpus:
        for src, dst in PAIRS:
            n += 1
            got = conv.convert(s["cells"][src], src, dst).text
            gold = s["cells"][dst]
            if got == gold:
                continue
            fails += 1
            gt, gd = got.split(), gold.split()
            if len(gt) != len(gd):
                cats["tokenisation(hyphen/spacing)"] += 1
                verdicts["rule-or-gold(structural)"] += 1
                if len(samples["tokenisation(hyphen/spacing)"]) < 4:
                    samples["tokenisation(hyphen/spacing)"].append((f"{src}->{dst}", got, gold))
                continue
            for a, b in zip(gt, gd):
                if a != b:
                    cat, verdict = classify_token(a, b, lex)
                    cats[cat] += 1
                    verdicts[verdict] += 1
                    if len(samples[cat]) < 4:
                        samples[cat].append((f"{src}->{dst}", a, b))
    return n, fails, cats, verdicts, samples


def detection(corpus):
    n = ok = 0
    cats = Counter()
    samples = defaultdict(list)
    for s in corpus:
        shared = defaultdict(set)
        for c in NORMS:
            shared[s["cells"][c]].add(c)
        for c in NORMS:
            text = s["cells"][c]
            n += 1
            r = detect(text, method="rules")
            if isinstance(r, NotPortuguese):
                cats["flagged-as-sister(false)"] += 1
                continue
            eid = r.id
            pred = ("pt_1973" if eid.startswith("pt_1973")
                    else "br_1971" if eid.startswith("br_1971") else eid)
            comp = shared[text]
            if pred in comp or (pred == "ao1990" and ({"ao1990-pt", "ao1990-br"} & comp)):
                ok += 1
                continue
            # categorise the miss
            if pred == "ao1990" and comp <= {"etymological", "pt_1973", "br_1971"}:
                cat = "under-detected-old(no marker in string)"
            elif pred in {"pt_1973", "br_1971"} and "ao1990-pt" in comp or "ao1990-br" in comp:
                cat = "over-detected-old(looks pre-AO90)"
            else:
                cat = "wrong-variant-or-era"
            cats[cat] += 1
            if len(samples[cat]) < 5:
                samples[cat].append((sorted(comp), pred, text))
    return n, ok, cats, samples


def main():
    corpus = load()
    conv = OrthographyConverter()
    lex = get_lexicon()

    print("=" * 70)
    print("CONVERSION (100% rules + lexicon; no model)")
    n, fails, cats, verdicts, samples = conversion(corpus, conv, lex)
    print(f"  {fails}/{n} conversions fail ({fails/n:.1%}); failing tokens by cause:\n")
    for cat, c in cats.most_common():
        print(f"    {cat:34} {c}")
    print("\n  verdict tally (per differing token):")
    for v, c in verdicts.most_common():
        print(f"    {v:34} {c}")
    print("\n  samples:")
    for cat in cats:
        for pair, a, b in samples[cat][:2]:
            print(f"    [{cat}] {pair}: got {a!r} / gold {b!r}")

    print("\n" + "=" * 70)
    print("DETECTION (rules method)")
    n, ok, cats, samples = detection(corpus)
    print(f"  {n-ok}/{n} renderings mis-detected ({(n-ok)/n:.1%}); by cause:\n")
    for cat, c in cats.most_common():
        print(f"    {cat:38} {c}")
    print("\n  samples:")
    for cat in cats:
        for comp, pred, text in samples[cat][:3]:
            print(f"    [{cat}] gold∈{comp} pred={pred}: {text}")


if __name__ == "__main__":
    main()
