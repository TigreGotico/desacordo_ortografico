"""The co-fator and co-factor rows of the pt-BR AO1990 map follow the ABL VOLP.

tugalex has the pt-BR cell "co-fator, co-factor" -> "cofator, cofactor". The table holds it
as the dual cell co-factor -> cofator|cofactor, beside the row co-fator -> cofator.

The ABL Vocabulário Ortográfico da Língua Portuguesa has one entry, to its end:
"cofator adj. s.m.". The searches "co-fat", "cofact" and "co-fact" give no row, so the
VOLP lists no co-fator, cofactor or co-factor. pt-BR writes cofator only, and both rows
give cofator.

For pt-PT the row cofactor -> cofator agrees with the Vocabulário Ortográfico do Português
(Portal da Língua Portuguesa). Its entry is, to its end: "cofator - nome masculino
co · fa · tor singular cofator plural cofatores Flexiona como : dor variante AO :
cofactor ( Brasil)". For pt-BR the ABL VOLP decides, and it lists no cofactor.

PR #33 already applies the VOLP last, so ao1990-br writes cofator before and after the
rows change.
"""
import json
from pathlib import Path

import pytest

import desacordo_ortografico
from desacordo_ortografico import convert
from desacordo_ortografico.convert import FEATURES
from desacordo_ortografico.lexicon import get_lexicon

_TABLE = Path(desacordo_ortografico.__file__).parent / "data" / "spelling.json"
_ROWS = ("co-fator", "co-factor")


def _rows(form):
    with open(_TABLE, encoding="utf-8") as f:
        return {(r["era"], r["target"]): r["value"] for r in json.load(f)["rows"] if r["form"] == form}


@pytest.mark.parametrize("form", _ROWS)
def test_the_row_gives_cofator(form):
    assert _rows(form) == {("br_1971", "ao1990-br"): "cofator"}


@pytest.mark.parametrize("form", _ROWS)
def test_the_map_alone_gives_cofator(form):
    # without the VOLP step, the table decides: a dual cell would give cofactor
    assert convert(form, "br_1971", "ao1990-br", features=FEATURES - {"volp"}) == "cofator"


def test_the_pt_br_map_has_no_cofator_dual():
    duals = get_lexicon().ao_br_dual_full
    assert {k: v for k, v in duals.items() if k.startswith("cofat")} == {}


@pytest.mark.parametrize("text,expected", [
    ("co-fator", "cofator"),
    ("co-factor", "cofator"),
    ("o cofator", "o cofator"),
    ("os cofatores e os cofactores", "os cofatores e os cofatores"),
])
def test_ao1990_br_writes_cofator_as_before(text, expected):
    assert convert(text, "br_1971", "ao1990-br") == expected


def test_pt_pt_writes_cofator():
    assert _rows("cofactor") == {("pt_1973", "ao1990-pt"): "cofator"}
    assert convert("o cofactor", "pt_1973", "ao1990-pt") == "o cofator"
