#!/usr/bin/env python3
"""Build ``desacordo_ortografico/data/spelling.json`` from the tugalex spelling lists.

    python tools/build_spelling_table.py [--curated-json reform_1911_irregular.json] [--out PATH]

The table took its rows from four sources, in this order:

1. the curated pre-1911 -> 1911 pairs (``curated`` true). ``--curated-json`` reads them from
   ``data/reform_1911_irregular.json`` of desacordo_ortografico 0.1.23a1 and earlier;
   without it the script keeps the curated rows of the table at ``--out``;
2. the rows of the tugalex ``archaisms.csv`` list. A row gives its modern pt-PT form, and
   that form can also carry a change made after 1911, so :func:`archaism_row_class` sorts
   the rows. A ``1911`` or ``ao1990-map`` row becomes a pre-1911 -> 1911 row when the
   Brazilian edges turn its 1911 form into its pt-BR form. Every other row gets rows for
   its AO1990 forms only;
3. the tugalex AO1990 pt-PT list (``acordo_ortografico_pt_PT.csv``), as pt_1973 rows;
4. the tugalex AO1990 pt-BR list (``acordo_ortografico_pt_BR.csv``), as br_1971 rows.

The script ran once, with the tugalex release that desacordo_ortografico pins as its
floor. People edit the table by hand from then on, like the other data files.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from functools import cached_property
from typing import Dict, List, Union

from tugalex import TugaLexicon

from desacordo_ortografico import rules
from desacordo_ortografico.convert import FEATURES, OrthographyConverter
from desacordo_ortografico.lexicon import Lexicon, deaccent

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE = os.path.join(HERE, "..", "desacordo_ortografico", "data", "spelling.json")
COLUMNS = ["form", "era", "target", "value", "curated", "source"]
ABOUT = (
    "The spelling facts that convert() and detect() read. Each row says that form, written "
    "in the norm era, is value in the norm target, on the authority of source. A dual "
    "AO1990 cell joins its two forms with '|', in source order. curated is true for the "
    "1911 pairs that the backward 1911 pass inverts and that detect() weighs double. A "
    "pre-1911 form whose 1911 form no source decides has rows for its AO1990 forms only. "
    "tools/build_spelling_table.py built the rows from the tugalex archaisms and AO1990 lists."
)
Row = Dict[str, Union[str, bool]]

#: The classes of a tugalex archaism row, see :func:`archaism_row_class`.
ARCHAISM_ROW_CLASSES = ("1911", "ao1990-map", "ao1990-cp", "ao1990-differential", "sc", "circumflex")

#: A Base IV 1º sequence of the AO1990 after a vowel: cc, cç, ct, pc, pç or pt.
_CP_SEQUENCE = re.compile(r"(?<=[aeiou])[cp][cçt]")


def archaism_row_class(archaic: str, modern: str, lex: Lexicon) -> str:
    """Classify a tugalex archaism row (``archaic`` -> its modern pt-PT form ``modern``)
    by the reform that its modern form rests on.

    ``1911``: no check below finds a post-1911 change, so the modern form stands for the
    1911 form (comsigo -> consigo, phosphoro -> fósforo). The checks do not find every
    accent: Base VII of 1911 writes "êle", and the row elle -> ele is in this class.
    ``ao1990-map``: the AO1990 pt-PT word map lists the modern form, so the 1911 form is the
    pre-AO1990 form of that map (architecto -> arquiteto, before AO1990 arquitecto).
    ``ao1990-differential``: the modern form is the bare form of a differential accent
    that the AO1990 dropped (pello -> pelo, before AO1990 pêlo).
    ``ao1990-cp``: the modern form lacks the c or p of a Base IV 1º sequence that the
    archaic form keeps after the regular 1911 rules, and the AO1990 map does not list it.
    1911 Base VIII drops such a consonant where it is silent (auctor -> autor), Base IX
    keeps it where it changes the vowel before it (affectando -> afectando, AO1990
    afetando), and no table here tells the two apart.
    ``sc``: the archaic form starts with the group sc and the modern form does not. Base
    XI of 1911 keeps that group (scena, sciência), and later accords drop it (cintilar).
    ``circumflex``: the archaic form has more ê or ô than the modern form. Base XXVIII
    of 1911 marks the closed e or o of a homograph ("rêgo, substantivo, e rego,
    verbo"), later laws drop that accent (sêcco -> seco, 1911 sêco), and no table here
    gives the 1911 form of every such row.

    Only the ``1911`` and ``ao1990-map`` rows can enter the 1911 word map.
    """
    if archaic.startswith("sc") and not modern.startswith("sc"):
        return "sc"
    if modern in lex.differential_dropped.values() or modern in lex.differential_restore:
        return "ao1990-differential"
    if modern in lex.ao_pt_new2old:
        return "ao1990-map"
    regular = rules.reform_1911_geminates(rules.reform_1911_digraphs(archaic))
    if len(_CP_SEQUENCE.findall(deaccent(regular))) > len(_CP_SEQUENCE.findall(deaccent(modern))):
        return "ao1990-cp"
    if _circumflexes(archaic) > _circumflexes(modern):
        return "circumflex"
    return "1911"


def _circumflexes(word: str) -> int:
    """The number of ê and ô in ``word``, the closed vowels of Base XXVIII."""
    return word.count("ê") + word.count("ô")


def row(form: str, era: str, target: str, value: str, curated: bool, source: str) -> Row:
    return dict(zip(COLUMNS, (form, era, target, value, curated, source)))


def curated_from_json(path: str) -> List[Row]:
    """The pairs of each group of the 1911 JSON, lowercased; a key seen again keeps its
    first position and takes the later value, as the dict of the old loader did."""
    pairs: Dict[str, Dict[str, str]] = {}
    with open(path, encoding="utf-8") as f:
        groups = json.load(f)
    for group, entries in groups.items():
        if group.startswith("_") or not isinstance(entries, dict):
            continue
        for k, v in entries.items():
            if k.startswith("_") or not isinstance(v, str):
                continue
            pairs[k.lower()] = row(k.lower(), "etymological", "reforma_1911", v.lower(), True,
                                   f"reform_1911_irregular.json ({group})")
    return list(pairs.values())


def curated_from_table(path: str) -> List[Row]:
    with open(path, encoding="utf-8") as f:
        return [r for r in json.load(f)["rows"] if r["curated"]]


def ao_rows(tuga: TugaLexicon) -> List[Row]:
    """The raw cells of both tugalex AO1990 lists, in file order."""
    out = []
    for cells, path, era, target in ((tuga.ao_pt, tuga.ao_pt_path, "pt_1973", "ao1990-pt"),
                                     (tuga.ao_br, tuga.ao_br_path, "br_1971", "ao1990-br")):
        for old, news in cells.items():
            assert not any("|" in n for n in news), (old, news)
            out.append(row(old, era, target, "|".join(news), False, f"tugalex {os.path.basename(path)}"))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--curated-json", help="reform_1911_irregular.json of desacordo 0.1.23a1")
    parser.add_argument("--out", default=TABLE)
    args = parser.parse_args()

    tuga = TugaLexicon()
    curated = curated_from_json(args.curated_json) if args.curated_json else curated_from_table(args.out)
    ao = ao_rows(tuga)

    class SourceLexicon(Lexicon):
        """The lexicon with the curated pairs and the AO1990 lists, before the archaisms."""

        @cached_property
        def _spelling(self) -> List[Row]:
            return curated + ao

    lex = SourceLexicon()
    edges = OrthographyConverter(lex)._edges

    def brazilian(word: str) -> str:
        for name in ("br_1911_to_1943", "accent_1971", "ao1990_br"):
            word = edges[name].forward.apply(word, FEATURES)
        return word

    notes = {}
    with open(tuga.archaisms_path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            notes[r["archaic"]] = f"tugalex archaisms.csv ({r['notes']})"

    curated_forms = {r["form"] for r in curated}
    to_1911, modern_only = [], []
    for archaic, modern in tuga.archaic_words.items():
        row_class = archaism_row_class(archaic, modern, lex)
        form = {"1911": modern, "ao1990-map": lex.ao_pt_new2old.get(modern)}.get(row_class)
        if form is not None and brazilian(form) == tuga.archaic_words_br[archaic]:
            if archaic not in curated_forms:
                to_1911.append(row(archaic, "etymological", "reforma_1911", form, False, notes[archaic]))
        elif archaic not in curated_forms:
            modern_only.append(row(archaic, "etymological", "ao1990-pt", modern, False, notes[archaic]))
            br = tuga.archaic_words_br[archaic]
            if br != modern:
                modern_only.append(row(archaic, "etymological", "ao1990-br", br, False, notes[archaic]))

    rows = curated + to_1911 + modern_only + ao
    # one row per line, so that a change to a row is a one-line diff
    lines = ",\n".join("    " + json.dumps(r, ensure_ascii=False) for r in rows)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(f'{{\n  "_about": {json.dumps(ABOUT, ensure_ascii=False)},\n  "rows": [\n{lines}\n  ]\n}}\n')
    print(f"archaisms in {len(tuga.archaic_words)}: to 1911 {len(to_1911)}, "
          f"AO1990 forms only {len({r['form'] for r in modern_only})}, "
          f"curated {len([a for a in tuga.archaic_words if a in curated_forms])}")
    print(f"rows written {len(rows)}: curated {len(curated)}, archaisms {len(to_1911) + len(modern_only)}, "
          f"AO1990 {len(ao)}")


if __name__ == "__main__":
    main()
