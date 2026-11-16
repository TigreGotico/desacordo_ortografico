"""pt-BR AO1990 rows whose word the ABL VOLP lists in both forms.

The tugalex pt-BR list gives each of these words one AO1990 form. The ABL Vocabulário
Ortográfico da Língua Portuguesa (VOLP) lists both forms as headwords:

- "bissetor (ô) adj. s.m." and "bissector (ô) adj. s.m."
- "foteletricidade s.f." and "fotelectricidade s.f."
- "idieletricidade s.f." and "idielectricidade s.f."
- "dactilozoide (ó) adj. s.m." and "datilozoide (ó) adj. s.m."

So each row is a dual cell, as the row datilozóide -> dactilozoide|datilozoide already is.
The first form of the cell stays first, so the single-form map and its reverse do not
change. The dual step then writes the form with the consonant where the VOLP step is off,
as Base IV 1º c and the dual rule of this library do.
"""
import json
from pathlib import Path

import pytest

import desacordo_ortografico
from desacordo_ortografico import convert
from desacordo_ortografico.convert import FEATURES
from desacordo_ortografico.lexicon import get_lexicon

_TABLE = Path(desacordo_ortografico.__file__).parent / "data" / "spelling.json"
ROWS = {
    "bissector": "bissetor|bissector",
    "fotelectricidade": "foteletricidade|fotelectricidade",
    "idielectricidade": "idieletricidade|idielectricidade",
    "dactilozóide": "dactilozoide|datilozoide",
}


def _br_cell(form):
    with open(_TABLE, encoding="utf-8") as f:
        return [r["value"] for r in json.load(f)["rows"] if r["form"] == form and r["era"] == "br_1971"]


@pytest.mark.parametrize("form, value", sorted(ROWS.items()))
def test_the_row_holds_both_volp_forms(form, value):
    assert _br_cell(form) == [value]


@pytest.mark.parametrize("bare, full", [
    ("bissetor", "bissector"),
    ("foteletricidade", "fotelectricidade"),
    ("idieletricidade", "idielectricidade"),
    ("datilozoide", "dactilozoide"),
])
def test_the_pt_br_dual_map_holds_the_pair(bare, full):
    assert get_lexicon().ao_br_dual_full[bare] == full


@pytest.mark.parametrize("form, expected", [
    ("bissector", "bissector"),
    ("bissetor", "bissector"),
    ("fotelectricidade", "fotelectricidade"),
    ("idielectricidade", "idielectricidade"),
    ("dactilozóide", "dactilozoide"),
])
def test_ao1990_br_writes_the_form_with_the_consonant(form, expected):
    assert convert(form, "br_1971", "ao1990-br") == expected
    assert convert(form, "br_1971", "ao1990-br", features=FEATURES - {"volp"}) == expected
