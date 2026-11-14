#!/usr/bin/env python3
"""Write Brazilian spellings in the Brazilian cells of the silver corpus.

Each line of ``variety_fixes.tsv`` gives a cell, a token, the pt_1973 token it stands
for (``*`` for any), the Brazilian form and its source. The pt_1973 token names the
word: the line for fato/facto changes "fato" only where the European cell writes
"facto", so the noun fato (a suit) stays. A line with ``*`` applies wherever the token
occurs. ``variety_drops.tsv`` lists tokens whose Brazilian form the sources cannot
decide; the script drops a row that holds one in that cell.

Sources, in order of authority:

- ABL, Vocabulário Ortográfico da Língua Portuguesa (VOLP), the official vocabulary of
  Brazil (https://www.academia.org.br/nossa-lingua/busca-no-vocabulario). Where it
  lists both forms of a word, the cell writes the c/p form (owner ruling on dual
  spellings). Two entries linked by "cf." with different glosses are two words.
- Dicionário Priberam da Língua Portuguesa, the Brazilian headword of the page, in the
  pre-AO1990 view for br_1971 and the post-AO1990 view for ao1990-br.
- Michaelis Moderno Dicionário da Língua Portuguesa.
- Formulário Ortográfico (ABL, 1943): the br_1971 cells write the preterite ending
  -amos without the accent. The ao1990-br cells keep -ámos, which the AO1990, Base IX,
  4 allows.

The tables are word-level, so the script also fixes rows that a later derivation adds.
Run it after ``build_corpus.py``, ``clean_silver.py`` and after the derived rows are
assembled into ``silver_full.jsonl``.

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
BRAZILIAN = ("br_1971", "ao1990-br")
_TOK = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[-'][0-9A-Za-zÀ-ɏ]+)*")


def load_table():
    table = {}
    with open(TABLE, encoding="utf-8") as f:
        next(f)
        for line in f:
            cell, token, european, correction, _source = line.rstrip("\n").split("\t")
            table.setdefault(cell, {})[(token, european)] = correction
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
    european = [t.lower() for t in _TOK.findall(rec["cells"].get("pt_1973", ""))]
    for cell in BRAZILIAN:
        fixes = table.get(cell, {})
        words = list(_TOK.finditer(rec["cells"][cell]))
        aligned = len(words) == len(european)
        out, end = [], 0
        for k, m in enumerate(words):
            word = m.group(0)
            token = word.lower()
            fix = (fixes.get((token, european[k])) if aligned else None) or fixes.get((token, "*"))
            if fix:
                counts[cell] += 1
            if cell == "br_1971" and (fix or token).endswith("ámos"):
                counts["br_1971 -amos"] += 1
                fix = (fix or token)[:-4] + "amos"
            out += [rec["cells"][cell][end:m.start()], _recase(fix, word) if fix else word]
            end = m.end()
            changed |= bool(fix)
        rec["cells"][cell] = "".join(out) + rec["cells"][cell][end:]
    return changed


def undecidable(rec, drops) -> bool:
    return any((cell, t.lower()) in drops for cell in BRAZILIAN
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
