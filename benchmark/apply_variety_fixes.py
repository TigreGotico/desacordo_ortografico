#!/usr/bin/env python3
"""Replace European spellings in the Brazilian cells of the silver corpus.

``variety_fixes.tsv`` lists, per cell, a token that a source gives for the other variety
only, the form of the cell's variety, and the source: the Priberam variety notes
("Grafia no Brasil", "Grafia em Portugal") or the Infopédia and Michaelis headwords.
Where both forms are attested in Brazil, the table writes the form with the c/p
consonant. The table is word-level, so the script also fixes rows that a later
derivation adds. Run it after ``build_corpus.py``, ``clean_silver.py`` and after the
derived rows are assembled into ``silver_full.jsonl``.

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
_TOK = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[-'][0-9A-Za-zÀ-ɏ]+)*")


def load_table():
    table = {}
    with open(TABLE, encoding="utf-8") as f:
        next(f)
        for line in f:
            cell, token, correction, _source = line.rstrip("\n").split("\t")
            table.setdefault(cell, {})[token] = correction
    return table


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
    return changed


def main(paths):
    table = load_table()
    for path in paths:
        with open(path, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        counts = Counter()
        n_changed = sum(fix_row(r, table, counts) for r in rows)
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
        print(f"{os.path.basename(path)}: rows in {len(rows)}, rows out {len(rows)}, "
              f"rows changed {n_changed}, tokens {dict(counts)}")


if __name__ == "__main__":
    args = sys.argv[1:] or [p for p in (os.path.join(HERE, "silver_corpus.jsonl"),
                                        os.path.join(HERE, "silver_full.jsonl"))
                            if os.path.exists(p)]
    main(args)
