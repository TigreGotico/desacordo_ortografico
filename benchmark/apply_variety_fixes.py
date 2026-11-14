#!/usr/bin/env python3
"""Write Brazilian spellings in the Brazilian cells of the silver corpus.

Each line of ``variety_fixes.tsv`` gives a cell, a token, the pt_1973 token it stands
for (``*`` for any), the Brazilian form, the rows it applies to (``*`` for all) and its
source. The pt_1973 token names the word: the line for fato/facto changes "fato" only
where the European cell writes "facto", so the noun fato (a suit) stays. A line that
names rows decides a token whose part of speech changes its spelling, such as the noun
reta and the adjective reta, or reaches a row whose Brazilian and pt_1973 cells differ in
token count. A capitalised token that does not start a sentence is a proper name (A
Otávia, o Ártico); the common-word entries do not cover it, so it stays as written.
``variety_drops.tsv`` lists tokens whose Brazilian form the sources cannot decide; the
script drops a row that holds one in that cell.

The br_1971 cell is the pre-1990 Brazilian norm. Its sources, in order of authority:

- ABL, Formulário Ortográfico (1943), with the changes of Lei 5.765/1971. Rule 18
  registers both forms of the words it lists ("contacto e contato", "secção e seção",
  "tecto e teto"), and the cell writes the c/p form of those (owner ruling on dual
  spellings). Rules 16 and 17 fix one form ("diretor ... ótimo ... e não ... director
  ... optimo"). Rule 43, 15.ª, OBSERVAÇÃO, writes the preterite ending -amos without
  the accent.
- Dicionário Priberam da Língua Portuguesa, the Brazilian headword in the view before
  the AO1990, for words the Formulário does not name. A page decides only when it shows
  a spelling change: before and after the AO1990 in Brazil or in Portugal, or between
  Brazil and Portugal before it. A page with one spelling in all four views decides
  nothing.
- If neither decides, the token stays as written.

The post-1990 VOLP never decides a br_1971 cell. The ao1990-br cell, in order:

- ABL, Vocabulário Ortográfico da Língua Portuguesa (VOLP), the official vocabulary of
  Brazil (https://www.academia.org.br/nossa-lingua/busca-no-vocabulario). Where it
  lists both forms of one word, with the same part of speech, the cell writes the c/p
  form. Two entries linked by "cf." with different glosses are two words. The cell
  keeps -ámos, which the AO1990, Base IX, 4 allows.
- Dicionário Priberam, the Brazilian headword in the view after the AO1990, where the
  page shows a spelling change. A page with one spelling in all four views records no
  spelling change, so it decides nothing.
- If neither decides, the token stays as written. A check list of Michaelis Moderno
  Dicionário headwords decides no further token.

Apart from the lines that name rows, the tables are word-level, so the script also
fixes rows that a later derivation adds.
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
            cell, token, european, correction, rows, _source = line.rstrip("\n").split("\t")
            for row in rows.split(","):
                table.setdefault(cell, {})[(token, european, row)] = correction
    return table


def load_drops():
    with open(DROPS, encoding="utf-8") as f:
        next(f)
        return {tuple(line.rstrip("\n").split("\t")[:2]) for line in f}


def _recase(form: str, like: str) -> str:
    if like.isupper() and len(like) > 1:
        return form.upper()
    return form[:1].upper() + form[1:] if like[:1].isupper() else form


def _is_name(text: str, m: re.Match) -> bool:
    before = text[:m.start()].rstrip(" \t\"'«“‘(—–-")
    return m.group(0)[:1].isupper() and bool(before) and before[-1] not in ".!?:…"


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
            row = rec.get("id")
            fix = None if _is_name(rec["cells"][cell], m) else (
                ((fixes.get((token, european[k], row)) or fixes.get((token, european[k], "*"))) if aligned else None)
                or fixes.get((token, "*", row)) or fixes.get((token, "*", "*")))
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
