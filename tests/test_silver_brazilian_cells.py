"""The Brazilian cells of the silver corpus write Brazilian spellings.

Sources, in order of authority: the ABL Vocabulário Ortográfico da Língua Portuguesa
(VOLP), the official vocabulary of Brazil; the Brazilian headword of the Dicionário
Priberam page; Michaelis. Where the VOLP lists both forms of a word, the cell writes the
c/p form (owner ruling on dual spellings). The Formulário Ortográfico of 1943, rule
15.ª, writes the preterite ending -amos without the accent, so br_1971 has no -ámos.
Each test names the entry it pins.
"""
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

import pytest

BENCHMARK = Path(__file__).parent.parent / "benchmark"
TOKEN = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[-'][0-9A-Za-zÀ-ɏ]+)*")
BRAZILIAN = ("br_1971", "ao1990-br")


def _rows():
    with (BENCHMARK / "silver_corpus.jsonl").open(encoding="utf-8") as f:
        return {row["id"]: row for row in map(json.loads, f)}


def _tsv(name):
    with (BENCHMARK / name).open(encoding="utf-8") as f:
        next(f)
        return [line.rstrip("\n").split("\t") for line in f]


def _tokens(row, cell):
    return [t.lower() for t in TOKEN.findall(row["cells"][cell])]


@pytest.mark.parametrize("cell", BRAZILIAN)
@pytest.mark.parametrize("row_id,word", [
    ("p03-020", "detectou"),   # VOLP: detectar v. | detetar v. (dual: the c/p form)
    ("p03-046", "detectou"),
    ("p04-003", "infecção"),   # VOLP: infecção s.f. | infeção s.f.
    ("p04-107", "infecção"),
    ("p11-076", "facções"),    # VOLP: facção s.f. | fação s.f.
    ("p01-024", "eléctron"),   # VOLP: eléctron s.m. | elétron s.m.
    ("p04-013", "óptica"),     # VOLP: óptica s.f. "ciência da visão"; cf. ótica ("ciência da audição")
    ("p09-056", "seção"),      # VOLP: seção s.f. "corte", etc.; Michaelis seção 6, a section of a shop
    ("p03-020", "inspeção"),   # VOLP: inspeção s.f.; no inspecção
])
def test_brazilian_cell_writes_the_source_form(row_id, cell, word):
    assert word in _tokens(_rows()[row_id], cell)


def _c_p_pairs(row, cell):
    """Tokens of the cell aligned with a pt_1973 token that is the same word plus one c/p."""
    european = _tokens(row, "pt_1973")
    tokens = _tokens(row, cell)
    if len(tokens) != len(european):
        return []
    plain = str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc")
    found = []
    for t, e in zip(tokens, european):
        a, b = t.translate(plain), e.translate(plain)
        if len(b) == len(a) + 1 and any(b[:i] + b[i + 1:] == a for i in range(len(b)) if b[i] in "cp"):
            found.append((t, e))
    return found


def test_every_bare_form_against_a_european_c_p_form_is_decided():
    """A Brazilian token that drops the c/p of its pt_1973 word either changes by a table
    line or stays by a line of variety_keeps.tsv that names its source."""
    keeps = {(t, e) for t, e, _reason in _tsv("variety_keeps.tsv")}
    gaps = sorted({(row_id, cell, t, e) for row_id, row in _rows().items() for cell in BRAZILIAN
                   for t, e in _c_p_pairs(row, cell) if (t, e) not in keeps})
    assert gaps == []


def test_br_1971_writes_amos_without_the_accent():
    found = [(row_id, t) for row_id, row in _rows().items()
             for t in _tokens(row, "br_1971") if t.endswith("ámos")]
    assert found == []


def test_no_row_holds_an_undecidable_token():
    drops = {(cell, token) for cell, token, _reason in _tsv("variety_drops.tsv")}
    found = [(row_id, cell, t) for row_id, row in _rows().items()
             for cell in BRAZILIAN for t in _tokens(row, cell) if (cell, t) in drops]
    assert found == []


def test_every_line_names_its_source():
    for cell, token, _european, fix, source in _tsv("variety_fixes.tsv"):
        assert cell in BRAZILIAN
        assert token != fix
        assert source.startswith(("VOLP: ", "Priberam ", "Michaelis: "))
    for _token, _european, reason in _tsv("variety_keeps.tsv"):
        assert reason.startswith(("VOLP: ", "Priberam ", "Michaelis: ", "no source: "))


def _apply_module():
    spec = importlib.util.spec_from_file_location("apply_variety_fixes",
                                                  BENCHMARK / "apply_variety_fixes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _apply(sentence, european):
    apply = _apply_module()
    row = {"cells": {"pt_1973": european, "br_1971": sentence, "ao1990-br": sentence}}
    apply.fix_row(row, apply.load_table(), Counter())
    return row["cells"]


def test_apply_writes_the_c_p_form_and_amos_only_in_br_1971():
    """VOLP: detectar v. | detetar v.; infecção s.f. | infeção s.f."""
    cells = _apply("Detetou a infeção e visitámos.", "Detectou a infecção e visitámos.")
    assert cells["br_1971"] == "Detectou a infecção e visitamos."
    assert cells["ao1990-br"] == "Detectou a infecção e visitámos."


def test_apply_reads_the_word_from_the_european_cell():
    """VOLP: facto s.m. | fato s.m. The fact is dual and takes the c/p form; the suit
    (pt_1973 fato) is another word and stays."""
    assert _apply("O fato é claro.", "O facto é claro.")["ao1990-br"] == "O facto é claro."
    assert _apply("O fato é azul.", "O fato é azul.")["ao1990-br"] == "O fato é azul."


def test_apply_keeps_a_single_brazilian_form():
    """VOLP: ação s.f., with no acção; seção s.f. "corte", etc. for a section of a shop."""
    cells = _apply("A ação da seção.", "A acção da secção.")
    assert cells["ao1990-br"] == "A ação da seção."


def test_apply_drops_a_row_with_an_undecidable_token():
    apply = _apply_module()
    row = {"cells": {"br_1971": "A detetiva chegou.", "ao1990-br": "A detetiva chegou."}}
    assert apply.undecidable(row, apply.load_drops())
