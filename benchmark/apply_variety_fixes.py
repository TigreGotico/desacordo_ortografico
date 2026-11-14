#!/usr/bin/env python3
"""Replace European spellings in the Brazilian cells of the silver corpus.

``variety_fixes.tsv`` lists, per cell, a token that a source gives for the other variety
only, the form of the cell's variety, and the source: the Priberam variety notes
("Grafia no Brasil", "Grafia em Portugal", kept in ``priberam_variety_notes.tsv``) or
the Infopédia and Michaelis headwords. Where both forms are valid in Brazil, the table
writes the form with the c/p consonant. ``variety_drops.tsv`` lists tokens whose
Brazilian form the sources cannot decide; a row that holds one in that cell is removed.
The br_1971 cells also write the first person plural of the preterite without the
accent (-amos), as the Formulário Ortográfico of 1943 prescribes; ao1990-br keeps
-ámos, which the AO1990 (Base IX, 4) allows. The tables are word-level, so the script
also fixes rows that a later derivation adds. Run it after ``build_corpus.py``,
``clean_silver.py`` and after the derived rows are assembled into ``silver_full.jsonl``.

    python benchmark/apply_variety_fixes.py [file.jsonl ...]   # default: silver_corpus.jsonl, silver_full.jsonl
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE = os.path.join(HERE, "variety_fixes.tsv")
DROPS = os.path.join(HERE, "variety_drops.tsv")
_TOK = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[-'][0-9A-Za-zÀ-ɏ]+)*")


def load_table():
    table = {}
    with open(TABLE, encoding="utf-8") as f:
        next(f)
        for line in f:
            cell, token, correction, _source = line.rstrip("\n").split("\t")
            table.setdefault(cell, {})[token] = correction
    return table


def load_drops():
    with open(DROPS, encoding="utf-8") as f:
        next(f)
        return {tuple(line.rstrip("\n").split("\t")[:2]) for line in f}


def _recase(form: str, like: str) -> str:
    if like.isupper() and len(like) > 1:
        return form.upper()
    return form[:1].upper() + form[1:] if like[:1].isupper() else form


def fix_row(rec, table, counts) -> bool:
    changed = False
    for cell, fixes in table.items():
        def repl(m, fixes=fixes, cell=cell):
            nonlocal changed
            fix = fixes.get(m.group(0).lower())
            if fix is None:
                return m.group(0)
            changed = True
            counts[cell] += 1
            return _recase(fix, m.group(0))
        rec["cells"][cell] = _TOK.sub(repl, rec["cells"][cell])

    def amos(m):
        nonlocal changed
        word = m.group(0)
        if not word.lower().endswith("ámos"):
            return word
        changed = True
        counts["br_1971 -amos"] += 1
        return word[:-4] + ("AMOS" if word.isupper() else "amos")
    rec["cells"]["br_1971"] = _TOK.sub(amos, rec["cells"]["br_1971"])
    return changed


def undecidable(rec, drops) -> bool:
    return any((cell, t.lower()) in drops for cell in ("br_1971", "ao1990-br")
               for t in _TOK.findall(rec["cells"][cell]))


def main(paths):
    table, drops = load_table(), load_drops()
    for path in paths:
        with open(path, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        kept = [r for r in rows if not undecidable(r, drops)]
        counts = Counter()
        n_changed = sum(fix_row(r, table, counts) for r in kept)
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in kept)
        print(f"{os.path.basename(path)}: rows in {len(rows)}, rows dropped {len(rows) - len(kept)}, "
              f"rows out {len(kept)}, rows changed {n_changed}, tokens {dict(counts)}")


if __name__ == "__main__":
    args = sys.argv[1:] or [p for p in (os.path.join(HERE, "silver_corpus.jsonl"),
                                        os.path.join(HERE, "silver_full.jsonl"))
                            if os.path.exists(p)]
    main(args)
