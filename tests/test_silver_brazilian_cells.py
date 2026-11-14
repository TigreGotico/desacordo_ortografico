"""The Brazilian cells of the silver corpus write Brazilian spellings.

Brazil writes and pronounces the consonant in infecção, facção and óptica. The forms come
from the "Grafia no Brasil" notes of the Dicionário Priberam pages of these words (post-
and pre-AO1990 views). Michaelis also lists ótica for Brazil, so óptica follows the dual
rule: where both forms are valid in the variety, the cell writes the c/p consonant.
"""
import json
import re
from pathlib import Path

import pytest

BENCHMARK = Path(__file__).parent.parent / "benchmark"
TOKEN = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[-'][0-9A-Za-zÀ-ɏ]+)*")


def _rows():
    with (BENCHMARK / "silver_corpus.jsonl").open(encoding="utf-8") as f:
        return {row["id"]: row for row in map(json.loads, f)}


def _fixes():
    with (BENCHMARK / "variety_fixes.tsv").open(encoding="utf-8") as f:
        next(f)
        return [line.rstrip("\n").split("\t") for line in f]


@pytest.mark.parametrize("row_id,cell,word", [
    ("p04-003", "ao1990-br", "infecção"),
    ("p04-107", "ao1990-br", "infecção"),
    ("p11-076", "ao1990-br", "facções"),
    ("p11-076", "br_1971", "facções"),
    ("p04-013", "ao1990-br", "óptica"),
    ("p04-013", "br_1971", "óptica"),
])
def test_brazilian_cell_writes_the_consonant(row_id, cell, word):
    tokens = [t.lower() for t in TOKEN.findall(_rows()[row_id]["cells"][cell])]
    assert word in tokens


def test_no_brazilian_cell_holds_a_listed_european_form():
    listed = {(cell, token) for cell, token, _fix, _source in _fixes()}
    found = sorted({(row_id, cell, t) for row_id, row in _rows().items()
                    for cell in ("br_1971", "ao1990-br")
                    for t in TOKEN.findall(row["cells"][cell]) if (cell, t.lower()) in listed})
    assert found == []


def test_every_fix_names_a_source_and_changes_the_word():
    for cell, token, fix, source in _fixes():
        assert cell in ("br_1971", "ao1990-br", "pt_1973", "ao1990-pt")
        assert token != fix
        assert source.startswith("Priberam ") or source == "Infopédia, Michaelis"
