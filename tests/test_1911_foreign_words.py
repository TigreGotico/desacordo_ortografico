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
