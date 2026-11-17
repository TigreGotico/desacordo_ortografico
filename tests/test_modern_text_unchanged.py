"""Text already valid in the target spelling goes through convert() unchanged.

A phonemizer runs desacordo over modern text before G2P, so a modern word that desacordo
rewrites becomes a wrong pronunciation. Each silver row of benchmark/silver_corpus.jsonl
whose pre-reform cell equals its AO1990 cell is a text that the reform left alone, and
convert() must leave it alone too: on the plain route (pt_1973 to ao1990-pt, br_1971 to
ao1990-br) and on the tugaphone spelling step, which calls
``convert(text, "etymological", <AO1990 norm>, features=<lect group>)``.

Where AO1990 makes two forms valid in the target variety, the converter writes the form
with the consonant. A word of that kind in modern text keeps its consonant.
"""
import json
from pathlib import Path

import pytest

from desacordo_ortografico import convert

# The feature groups of the tugaphone spelling step. pt-BR and pt-UY share the br group.
PT_GROUP = frozenset({"1911-word-map", "trema", "ao-map-consonant", "base-iv",
                      "initial-sc", "ao-map-diacritic"})
BR_GROUP = frozenset({"1911-word-map", "base-iv", "initial-sc", "ptbr-divergence",
                      "hyphen-lexical"})

# Words that each group rewrites only because the dual guard sits in the silent-cp feature
# (pt group) or the volp feature (br group), which the group leaves out.
PT_DUAL_GUARD = {"sector", "carácter", "acupunctura"}
BR_DUAL_GUARD = {"contacto", "contactar"}
# The etymological route to ao1990-br drops the p of óptica, which the repo pins in both
# Brazilian cells of row p04-013.
BR_OPTICA = {"óptica"}


# Row p12-064 writes "decepcionou" in its pt_1973 and ao1990-pt cells, but AO1990 pt-PT
# writes dececionou: VOP lemma 54366 "decepcionar - verbo ... Brasil ... variante AO de :
# dececionar ( Portugal)", lemma 191820 "dececionar - verbo ... Portugal", conjugated
# "dececionou". The cell is not modern pt-PT text, so the row stays out of the selection.
NOT_AO1990_PT = {"p12-064"}


def _unchanged_cells(old, new):
    """(row id, cell) of each distinct silver cell that ``old`` and ``new`` write alike."""
    path = Path(__file__).parent.parent / "benchmark" / "silver_corpus.jsonl"
    seen = {}
    for line in path.open(encoding="utf-8"):
        row = json.loads(line)
        cells = row["cells"]
        if cells[old] == cells[new] and not (new == "ao1990-pt" and row["id"] in NOT_AO1990_PT):
            seen.setdefault(cells[new], row["id"])
    return [(row_id, cell) for cell, row_id in seen.items()]


PT_CELLS = _unchanged_cells("pt_1973", "ao1990-pt")
BR_CELLS = _unchanged_cells("br_1971", "ao1990-br")


def _params(cells, xfails=None):
    params = []
    for row_id, cell in cells:
        marks = ()
        words = {w.strip(".,;:!?«»").lower() for w in cell.split()}
        for reason, keys in (xfails or {}).items():
            if words & keys:
                marks = pytest.mark.xfail(strict=True, reason=reason)
        params.append(pytest.param(cell, id=row_id, marks=marks))
    return params


def test_silver_selection_counts():
    assert (len(PT_CELLS), len(BR_CELLS)) == (758, 788)


@pytest.mark.xfail(strict=True, reason="desacordo#74")
@pytest.mark.parametrize("source, features", [("pt_1973", None), ("etymological", PT_GROUP)])
def test_pt_routes_write_dececionou(source, features):
    text = "O ténue crescimento decepcionou os economistas."
    expected = "O ténue crescimento dececionou os economistas."
    assert convert(text, source, "ao1990-pt", features=features) == expected


@pytest.mark.parametrize("cell", _params(PT_CELLS))
def test_pt_1973_text_stays_at_ao1990_pt(cell):
    assert convert(cell, "pt_1973", "ao1990-pt") == cell


@pytest.mark.parametrize("cell", _params(BR_CELLS))
def test_br_1971_text_stays_at_ao1990_br(cell):
    assert convert(cell, "br_1971", "ao1990-br") == cell


@pytest.mark.parametrize("cell", _params(PT_CELLS))
def test_pt_group_keeps_modern_text(cell):
    assert convert(cell, "etymological", "ao1990-pt", features=PT_GROUP) == cell


@pytest.mark.parametrize("cell", _params(BR_CELLS, {"desacordo#65": BR_DUAL_GUARD,
                                                    "desacordo#69": BR_OPTICA}))
def test_br_group_keeps_modern_text(cell):
    assert convert(cell, "etymological", "ao1990-br", features=BR_GROUP) == cell


# pt-PT words valid after AO1990, each quoted from its lemma in the VOP (Vocabulário
# Ortográfico do Português, Portal da Língua Portuguesa). The VOP tags óptica, conjectura,
# epiléptico and cacto as Brasil forms (pt-PT ótica, conjetura, epilético, cato) and has
# no ceptro, so none of them is a pt-PT word here.
PT_PT_WORDS = [
    # lemma 47603: "sector - nome masculino ... variante AO de : setor"
    "sector",
    # lemma 48215: "carácter - nome masculino ... Portugal ... variante AO de : caráter"
    "carácter",
    # lemma 106786: "acupunctura - nome feminino ... variante AO de : acupuntura"
    "acupunctura",
    # lemma 7358: "facto - nome masculino ... variante AO : fato"
    "facto",
    # lemma 55919: "secção - nome feminino ... variante AO de : seção ( Brasil)"
    "secção",
    # lemma 11164: "amígdala - nome feminino ... variante AO : amídala ( Brasil)"
    "amígdala",
    # lemma 138104: "quotidiano - nome masculino ... variante de : cotidiano"
    "quotidiano",
]


@pytest.mark.parametrize("word", PT_PT_WORDS)
def test_pt_pt_word_stays_at_ao1990_pt(word):
    assert convert(word, "pt_1973", "ao1990-pt") == word


@pytest.mark.parametrize("word", _params([(w, w) for w in PT_PT_WORDS],
                                          {"desacordo#65": PT_DUAL_GUARD}))
def test_pt_group_keeps_pt_pt_word(word):
    assert convert(word, "etymological", "ao1990-pt", features=PT_GROUP) == word
