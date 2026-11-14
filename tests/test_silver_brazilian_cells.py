"""The Brazilian cells of the silver corpus write Brazilian spellings.

Brazil writes and pronounces the consonant in infecção, facção and detectar. The forms
come from the "Grafia no Brasil" and "Grafia em Portugal" notes of the Dicionário
Priberam pages of these words, pre- and post-AO1990 views, which
``benchmark/priberam_variety_notes.tsv`` keeps. Michaelis also lists ótica and seção for
Brazil, so óptica and secção follow the dual rule: where both forms are valid in the
variety, the cell writes the c/p consonant. The 1943 Formulário Ortográfico writes the
preterite ending -amos without the accent, so br_1971 has no -ámos form.
"""
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

import pytest

BENCHMARK = Path(__file__).parent.parent / "benchmark"
TOKEN = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[-'][0-9A-Za-zÀ-ɏ]+)*")
ERAS = {"br_1971": "pre", "ao1990-br": "post"}


def _rows():
    with (BENCHMARK / "silver_corpus.jsonl").open(encoding="utf-8") as f:
        return {row["id"]: row for row in map(json.loads, f)}


def _tsv(name):
    with (BENCHMARK / name).open(encoding="utf-8") as f:
        next(f)
        return [line.rstrip("\n").split("\t") for line in f]


def _tokens(row, cell):
    return [t.lower() for t in TOKEN.findall(row["cells"][cell])]


@pytest.mark.parametrize("row_id,cell,word", [
    ("p04-003", "ao1990-br", "infecção"),
    ("p04-107", "ao1990-br", "infecção"),
    ("p11-076", "ao1990-br", "facções"),
    ("p11-076", "br_1971", "facções"),
    ("p04-013", "ao1990-br", "óptica"),
    ("p04-013", "br_1971", "óptica"),
    ("p03-020", "ao1990-br", "detectou"),
    ("p03-020", "br_1971", "detectou"),
    ("p03-046", "ao1990-br", "detectou"),
    ("p03-046", "br_1971", "detectou"),
    ("p09-056", "ao1990-br", "secção"),
    ("p09-056", "br_1971", "secção"),
])
def test_brazilian_cell_writes_the_consonant(row_id, cell, word):
    assert word in _tokens(_rows()[row_id], cell)


def _european_only():
    """Per era: each form a Priberam page gives for Portugal only, and the Brazilian forms.

    A view with no note for one variety writes the other variety's form in it.
    """
    euro = {"pre": set(), "post": set()}
    brazil = {"pre": set(), "post": set()}
    for _page, *cols in _tsv("priberam_variety_notes.tsv"):
        notes = dict(zip(("PT_pre", "PT_post", "BR_pre", "BR_post"),
                         (set(c.split("|")) - {""} for c in cols)))
        for era in ("pre", "post"):
            pt = notes[f"PT_{era}"] or notes[f"BR_{era}"]
            br = notes[f"BR_{era}"] or notes[f"PT_{era}"]
            euro[era] |= pt - br
            brazil[era] |= br
    return euro, brazil


def _common(a, b):
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    return n


def test_no_brazilian_cell_writes_a_form_priberam_gives_portugal_only():
    """A token that is a Portugal-only form, or an inflection of one, is a gap in the table.

    An inflection shares all but the last two letters of the form. A token closer to a
    Brazilian form of the same view (a longer common start) is that Brazilian word, for
    example detetive next to the Portugal-only detetiva. A form that the dual rule writes
    (secção: Priberam gives Brazil seção, Michaelis lists secção) names both sources in
    its table line.
    """
    euro, brazil = _european_only()
    dual = {(cell, fix) for cell, _token, fix, source in _tsv("variety_fixes.tsv")
            if source.startswith("dual rule: ")}
    found = set()
    for row_id, row in _rows().items():
        for cell, era in ERAS.items():
            for t in set(_tokens(row, cell)) - {fix for c, fix in dual if c == cell}:
                for p in euro[era]:
                    stem = p[:-2]
                    if t != p and not (len(stem) >= 4 and t.startswith(stem) and len(t) <= len(p) + 3):
                        continue
                    if not any(_common(t, b) > _common(t, p) for b in brazil[era]):
                        found.add((row_id, cell, t, p))
    assert sorted(found) == []


def test_br_1971_writes_amos_without_the_accent():
    found = [(row_id, t) for row_id, row in _rows().items()
             for t in _tokens(row, "br_1971") if t.endswith("ámos")]
    assert found == []


def test_no_row_holds_an_undecidable_token():
    drops = {(cell, token) for cell, token, _reason in _tsv("variety_drops.tsv")}
    found = [(row_id, cell, t) for row_id, row in _rows().items()
             for cell in ERAS for t in _tokens(row, cell) if (cell, t) in drops]
    assert found == []


def test_every_fix_names_a_source_and_changes_the_word():
    for cell, token, fix, source in _tsv("variety_fixes.tsv"):
        assert cell in ERAS
        assert token != fix
        assert source.startswith(("Priberam ", "Infopédia ", "dual rule: ", "restore: "))


def _apply_module():
    spec = importlib.util.spec_from_file_location("apply_variety_fixes",
                                                  BENCHMARK / "apply_variety_fixes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_apply_writes_the_table_form_and_amos_only_in_br_1971():
    apply = _apply_module()
    sentence = "Detetámos a infeção."
    row = {"cells": {"etymological": sentence, "pt_1973": sentence, "ao1990-pt": sentence,
                     "br_1971": sentence, "ao1990-br": sentence}}
    assert apply.fix_row(row, apply.load_table(), Counter())
    assert row["cells"]["br_1971"] == "Detectamos a infecção."
    assert row["cells"]["ao1990-br"] == "Detectámos a infecção."
    assert row["cells"]["ao1990-pt"] == sentence


def test_apply_drops_a_row_with_an_undecidable_token():
    apply = _apply_module()
    row = {"cells": {"br_1971": "A detetiva chegou.", "ao1990-br": "A detetiva chegou."}}
    assert apply.undecidable(row, apply.load_drops())
