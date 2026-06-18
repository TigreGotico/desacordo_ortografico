#!/usr/bin/env python3
"""Benchmark desacordo_ortografico against the parallel gold corpus.

Measures conversion (directed norm pairs, overall + per feature family), detection
(compatible accuracy + a nominal confusion matrix), and the sister-language guard.
Writes ``results.md`` and ``results.json`` (the latter feeds ``plot_results.py``).

    python benchmark/run_benchmark.py [--corpus gold_corpus.jsonl]
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict

from desacordo_ortografico import OrthographyConverter, detect
from desacordo_ortografico.guard import NotPortuguese

HERE = os.path.dirname(os.path.abspath(__file__))
NORMS = ["etymological", "pt_1973", "ao1990-pt", "br_1971", "ao1990-br"]
CONVERSION_PAIRS = [
    ("etymological", "pt_1973"),
    ("etymological", "ao1990-pt"),
    ("etymological", "ao1990-br"),
    ("pt_1973", "ao1990-pt"),
    ("br_1971", "ao1990-br"),
    ("ao1990-pt", "ao1990-br"),
    ("ao1990-br", "ao1990-pt"),
]


def _load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _norm_feature(f):
    """Collapse the agents' free-form feature tags into canonical families."""
    f = f.lower()
    table = [
        ("digraph", "digraph"), ("ch-k", "ch_k"), ("ch_k", "ch_k"), ("hymn", "digraph"),
        ("geminate", "geminate"), ("silent-ct", "silent_ct"), ("silent-pt", "silent_pt"),
        ("nasal", "nasal"), ("trema", "trema"), ("diphthong", "diphthong"),
        ("paroxytone", "diphthong"), ("oo", "diphthong"), ("eem", "diphthong"),
        ("differential", "differential"), ("dual", "dual"), ("divergence", "divergence"),
        ("humido", "divergence"), ("connosco", "divergence"), ("amnistia", "divergence"),
        ("subtil", "divergence"), ("umido", "divergence"), ("conosco", "divergence"),
        ("cotidiano", "divergence"), ("registro", "divergence"), ("rececao", "dual"),
        ("month", "months"), ("hyphen", "hyphen_rs"), ("mn", "mn_ps"), ("ps-", "mn_ps"),
        ("egipcio", "silent_ct"), ("k-w", "digraph"), ("y", "digraph"),
    ]
    for needle, fam in table:
        if needle in f:
            return fam
    return f


def _bucket(text):
    """detect() -> (compatible column set, nominal bucket, NotPortuguese?)."""
    r = detect(text)
    if isinstance(r, NotPortuguese):
        return set(), "not-portuguese", r
    eid = r.id
    if eid.startswith("etymological"):
        return {"etymological"}, "etymological", r
    if eid.startswith("pt_1973"):
        return {"pt_1973"}, "pt_1973", r
    if eid.startswith("br_1971"):
        return {"br_1971"}, "br_1971", r
    if eid == "ao1990-pt":
        return {"ao1990-pt"}, "ao1990-pt", r
    if eid == "ao1990-br":
        return {"ao1990-br"}, "ao1990-br", r
    if eid == "ao1990":
        return {"ao1990-pt", "ao1990-br"}, "ao1990", r
    return {eid}, eid, r


def _tok_acc(pred, gold):
    p, g = pred.split(), gold.split()
    if not g:
        return 1.0
    return sum(a == b for a, b in zip(p, g)) / max(len(g), len(p))


def run(corpus="gold_corpus.jsonl"):
    parallel = _load(corpus)
    sisters = _load("gold_sisters.jsonl")
    conv = OrthographyConverter()
    res = {"corpus": corpus, "n": len(parallel)}

    # -------- conversion: per pair + per feature ----------
    pair_stats = {}
    feat_hit = defaultdict(int)
    feat_tot = defaultdict(int)
    tot_exact = tot_n = 0
    tok_sum = 0.0
    examples = []
    for src, dst in CONVERSION_PAIRS:
        exact = n = 0
        tacc = 0.0
        for s in parallel:
            g_src, g_dst = s["cells"][src], s["cells"][dst]
            pred = conv.convert(g_src, src, dst).text
            n += 1
            tacc += _tok_acc(pred, g_dst)
            ok = pred == g_dst
            exact += ok
            for ft in {_norm_feature(f) for f in s.get("features", [])}:
                feat_tot[ft] += 1
                feat_hit[ft] += ok
            if not ok and len(examples) < 40:
                examples.append({"pair": f"{src}->{dst}", "id": s["id"],
                                 "in": g_src, "got": pred, "gold": g_dst})
        pair_stats[f"{src}->{dst}"] = {"exact": exact, "n": n, "token_acc": tacc / n}
        tot_exact += exact
        tot_n += n
        tok_sum += tacc
    res["conversion"] = {
        "overall_exact": tot_exact / tot_n, "overall_token": tok_sum / tot_n,
        "n_conversions": tot_n, "by_pair": pair_stats,
        "by_feature": {ft: feat_hit[ft] / feat_tot[ft] for ft in sorted(feat_tot)},
        "by_feature_n": {ft: feat_tot[ft] for ft in sorted(feat_tot)},
        "examples": examples,
    }

    # -------- detection: compatible accuracy + confusion ----------
    det_ok = det_n = 0
    confusion = defaultdict(Counter)  # nominal column -> predicted bucket
    for s in parallel:
        cells = s["cells"]
        shared = defaultdict(set)
        for col in NORMS:
            shared[cells[col]].add(col)
        for col in NORMS:
            compat, nominal, _ = _bucket(cells[col])
            expected = shared[cells[col]]  # columns sharing this exact string
            det_n += 1
            det_ok += bool(compat & expected)
            confusion[col][nominal] += 1
    res["detection"] = {
        "compatible_acc": det_ok / det_n, "n": det_n,
        "confusion": {k: dict(v) for k, v in confusion.items()},
    }

    # -------- guard ----------
    g_ok = g_n = 0
    g_conf = defaultdict(Counter)
    for s in sisters:
        r = detect(s["text"])
        flagged = isinstance(r, NotPortuguese)
        got = r.lang if flagged else "portuguese"
        g_conf[s["lang"]][got] += 1
        g_n += 1
        g_ok += (not flagged) if s["is_portuguese"] else (flagged and r.lang == s["lang"])
    res["guard"] = {"acc": g_ok / g_n, "n": g_n,
                    "confusion": {k: dict(v) for k, v in g_conf.items()}}

    return res


def write_md(res):
    L = []
    a = L.append
    a("# desacordo_ortografico benchmark\n")
    a(f"Corpus: `{res['corpus']}` — {res['n']} parallel sentences "
      f"({res['n'] * 5} renderings across 5 norms).\n")
    c = res["conversion"]
    a("## Conversion\n")
    a("| pair | exact-match | token-acc |")
    a("|------|-------------|-----------|")
    for pair, st in c["by_pair"].items():
        a(f"| {pair} | {st['exact']}/{st['n']} = {st['exact']/st['n']:.1%} | {st['token_acc']:.1%} |")
    a(f"\n**Overall: {c['overall_exact']:.1%} exact-match, {c['overall_token']:.1%} "
      f"token-accuracy over {c['n_conversions']} conversions.**\n")
    a("### Conversion accuracy by feature family\n")
    a("| feature | exact-match | n |")
    a("|---------|-------------|---|")
    for ft in sorted(c["by_feature"], key=lambda k: c["by_feature"][k]):
        a(f"| {ft} | {c['by_feature'][ft]:.1%} | {c['by_feature_n'][ft]} |")
    d = res["detection"]
    a(f"\n## Detection\n\n**Compatible accuracy: {d['compatible_acc']:.1%}** "
      f"over {d['n']} renderings.\n")
    a("Confusion (nominal norm -> predicted, raw counts; off-diagonal often reflects "
      "norms that are spelling-identical for a given sentence):\n")
    preds = sorted({p for v in d["confusion"].values() for p in v})
    a("| nominal \\ predicted | " + " | ".join(preds) + " |")
    a("|" + "---|" * (len(preds) + 1))
    for col in NORMS:
        row = d["confusion"].get(col, {})
        a(f"| {col} | " + " | ".join(str(row.get(p, 0)) for p in preds) + " |")
    g = res["guard"]
    a(f"\n## Sister-language guard\n\n**Accuracy: {g['acc']:.1%}** over {g['n']} samples.\n")
    a("## Summary\n")
    a(f"- conversion exact-match: **{c['overall_exact']:.1%}**")
    a(f"- conversion token-accuracy: **{c['overall_token']:.1%}**")
    a(f"- detection compatible accuracy: **{d['compatible_acc']:.1%}**")
    a(f"- guard accuracy: **{g['acc']:.1%}**")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="gold_corpus.jsonl")
    args = ap.parse_args()
    res = run(args.corpus)
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    md = write_md(res)
    with open(os.path.join(HERE, "results.md"), "w", encoding="utf-8") as f:
        f.write(md + "\n")
    print(md)


if __name__ == "__main__":
    main()
