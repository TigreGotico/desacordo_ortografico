"""The 1911 rule fallbacks leave loanwords and foreign names alone.

AO1990 Base I 2º keeps k, w and y in foreign names and their derivatives, and Base I 3º
keeps the spelling of a foreign name in its derivatives. The examples below are the
examples of those clauses. The gold rows are rows of the parallel gold corpus.
"""
import json
from pathlib import Path

import pytest

from desacordo_ortografico import convert

TARGETS = ("pt_1973", "ao1990-pt", "br_1971", "ao1990-br")

# AO1990 Base I 2º a), 2º b) and 3º, verbatim examples
BASE_I = ["Franklin", "frankliniano", "Kant", "kantismo", "Darwin", "darwinismo",
          "Wagner", "wagneriano", "Taylor", "taylorista", "Kwanza", "Kuwait",
          "kuwaitiano", "Malawi", "malawiano", "shakesperiano"]


@pytest.mark.parametrize("word", BASE_I + ["Hollywood"])
@pytest.mark.parametrize("target", TARGETS)
def test_foreign_name_and_derivative_keep_their_spelling(word, target):
    assert convert(f"o {word}", "etymological", target) == f"o {word}"


@pytest.mark.parametrize("target", TARGETS)
def test_portuguese_place_name_keeps_its_spelling(target):
    # gold_full.jsonl row d00069 (Hugging Face dataset TigreGotico/desacordo_ortografico)
    text = "Sentia-se afectada cada vez que ouvia aquela velha canção de Coimbra."
    assert convert(text, "etymological", target).endswith(" de Coimbra.")


def _gold_parallel(row_id):
    path = Path(__file__).parent.parent / "benchmark" / "gold_parallel.jsonl"
    for line in path.open(encoding="utf-8"):
        row = json.loads(line)
        if row["id"] == row_id:
            return row["cells"]
    raise KeyError(row_id)


@pytest.mark.parametrize("row_id", ["s02", "s03"])
@pytest.mark.parametrize("target", TARGETS)
def test_etymological_words_still_convert(row_id, target):
    cells = _gold_parallel(row_id)
    assert convert(cells["etymological"], "etymological", target) == cells[target]


# AO1990 Base XI 1º b): proparoxytones in -ie take the accent ("barbárie, série").
# espécie and superfície are the modern cells of gold_full.jsonl, and efígie follows the
# same clause after the 1911 reduction of ff.
IE_NOUNS = [("especie", "espécie"), ("serie", "série"), ("superficie", "superfície"),
            ("effigie", "efígie")]


@pytest.mark.parametrize("old, new", IE_NOUNS)
@pytest.mark.parametrize("target", TARGETS)
def test_portuguese_noun_in_ie_still_converts(old, new, target):
    assert convert(f"a {old}", "etymological", target) == f"a {new}"


# The present subjunctive of anunciar and apreciar (both in the tugalex word list) ends
# in -ie; the 1911 reform reduces nn and pp.
@pytest.mark.parametrize("old, new", [("annuncie", "anuncie"), ("apprecie", "aprecie")])
@pytest.mark.parametrize("target", TARGETS)
def test_iar_subjunctive_still_converts(old, new, target):
    assert convert(f"que ele {old}", "etymological", target) == f"que ele {new}"


# fósforo takes the accent since 1911 (gold_parallel.jsonl row s01: fósforos). An opening
# quote is no sign of a proper name.
def test_word_after_an_opening_quote_still_restores_the_accent():
    text = "«Fosforo», gritou ele."
    assert convert(text, "etymological", "pt_1973") == "«Fósforo», gritou ele."


# Text in capitals shows no proper names, so fósforo still takes its accent.
def test_text_in_capitals_still_restores_the_accent():
    text = "A PHARMACIA DO FOSFORO"
    assert convert(text, "etymological", "pt_1973") == "A FARMÁCIA DO FÓSFORO"
