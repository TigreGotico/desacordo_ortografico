#!/usr/bin/env python3
"""Tighten the gold corpus to reference quality — safely.

The five cells of a sentence are NOT all orthographic variants of one another: the
European line (etymological, pt_1973, ao1990-pt) and the Brazilian line (br_1971,
ao1990-br) may legitimately differ in *lexis* (ficheiro/arquivo, utilizador/usuário).
So consistency is checked **within each line**, where the cells differ only by the
documented era transforms (which the skeleton folds).

To avoid ever corrupting the reference, this tool does exactly two things:

1. **Correct AO1990 cells only** — force a dual/divergence word to the right variant in
   the (unambiguous) modern cells (`receptor`->`recetor` in ao1990-pt). Pre-AO1990 cells
   are never touched, because their forms are era-dependent.
2. **Drop, never fix** — any sentence whose European *or* Brazilian line is internally
   inconsistent (an article slip, a different word, a token-count mismatch) is removed.

The result is a corpus where every line is provably self-consistent.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter

from desacordo_ortografico.lexicon import deaccent, get_lexicon

HERE = os.path.dirname(os.path.abspath(__file__))
_TOK = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[-'][0-9A-Za-zÀ-ɏ]+)*")


def skel(tok: str) -> str:
    """Fold a token to an orthography-invariant skeleton (aggressive on purpose)."""
    t = re.sub(r"[-'’]", "", tok.lower())
    t = deaccent(t)
    t = re.sub(r"^e(?=s[bcdfgpqt])", "", t)   # prothetic e: esfera<->sphera, estilo<->stylo
    t = t.replace("ph", "f").replace("th", "t").replace("rh", "r")
    t = t.replace("ch", "c").replace("qu", "c").replace("k", "c").replace("q", "c")
    t = t.replace("sc", "c").replace("y", "i")  # sciencia<->ciência
    for p, r in (("cç", "ç"), ("ct", "t"), ("pç", "ç"), ("pt", "t"), ("pc", "c")):
        t = t.replace(p, r)
    t = t.replace("ü", "u").replace("mn", "n").replace("ps", "s")
    t = t.replace("mf", "nf").replace("str", "st").replace("ç", "c")  # triumpho<->triunfo
    t = re.sub(r"(.)\1+", r"\1", t)
    return t.lstrip("h")


def _capitalise(form: str, like: str) -> str:
    return form[:1].upper() + form[1:] if like[:1].isupper() else form


def correct_ao90(rec, lex) -> int:
    """Pass 1: force dual/divergence words to the right variant in the modern cells."""
    n = 0
    plan = [("ao1990-pt", lex.dual_br2pt, lex.divergence_br2pt),
            ("ao1990-br", lex.dual_pt2br, lex.divergence_pt2br)]
    for norm, dmap, vmap in plan:
        def repl(m, dmap=dmap, vmap=vmap):
            nonlocal n
            w = m.group(0)
            fix = dmap.get(w.lower()) or vmap.get(w.lower())
            if fix:
                n += 1
                return _capitalise(fix, w)
            return w
        rec["cells"][norm] = _TOK.sub(repl, rec["cells"][norm])
    return n


def cells_consistent(rec, cells) -> bool:
    """Rigorous: every cell's tokens fold to the same skeleton at each position."""
    toks = [_TOK.findall(rec["cells"][nm]) for nm in cells]
    if len({len(t) for t in toks}) != 1:
        return False
    for pos in range(len(toks[0])):
        if len({skel(toks[i][pos]) for i in range(len(cells))}) != 1:
            return False
    return True


def etym_ok(rec) -> bool:
    """The etymological cell is harder to fold (open-ended transforms), so it is only
    rejected for a *short-word* mismatch (an article slip) or a clearly *different word*
    (skeletons sharing no 3-letter prefix). Long unfolded transforms (electron/eletrão,
    symptoma/sintoma, -aes/-ais) are tolerated."""
    et = _TOK.findall(rec["cells"]["etymological"])
    pt = _TOK.findall(rec["cells"]["pt_1973"])
    if len(et) != len(pt):
        return False
    for a, b in zip(et, pt):
        sa, sb = skel(a), skel(b)
        if sa != sb and (max(len(a), len(b)) <= 3 or sa[:3] != sb[:3]):
            return False
    return True


def main():
    lex = get_lexicon()
    corpus = [json.loads(line) for line in open(os.path.join(HERE, "gold_corpus.jsonl"),
                                                encoding="utf-8") if line.strip()]
    out = []
    stats = Counter()
    for rec in corpus:
        stats["ao90_variant_fixes"] += correct_ao90(rec, lex)
        if (cells_consistent(rec, ["pt_1973", "ao1990-pt"])
                and cells_consistent(rec, ["br_1971", "ao1990-br"])
                and etym_ok(rec)):
            out.append(rec)
        else:
            stats["dropped"] += 1

    with open(os.path.join(HERE, "gold_corpus.jsonl"), "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"input sentences:           {len(corpus)}")
    print(f"AO1990 variant fixes:      {stats['ao90_variant_fixes']}")
    print(f"dropped (line-inconsistent):{stats['dropped']}")
    print(f"clean corpus:              {len(out)} sentences ({len(out) * 5} renderings)")


if __name__ == "__main__":
    main()
