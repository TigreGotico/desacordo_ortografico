"""The pre-1911 rows that the Formulário Ortográfico of 1911 decides.

Each expected form comes from a clause, not from the converter:

- kilo is a 1911 spelling. Base I, Excepção 2.ª: "e tambêm na forma international kilo, que
  todavia se poderá escrever quilo". Later norms write quilo. The Bases of 1931, § 2.º:
  "Substituir: 1.º O k e o grupo ch (duro), por qu, antes de e e i, e por c, nos outros
  casos: querubim, monarca, quimica, quilo". Formulário Ortográfico of 1943, 3.: "O k é
  substituído por qu antes de e, i".
- scena and sciência are 1911 spellings. Base XI: "É conservado o grupo inicial sc, das
  seguintes palavras e seus derivados e afins, em que o s é mudo: scena, sciência, scetro".
  1943, 19.: "Elimina-se o s do grupo inicial sc: celerado, cena, cenografia, ciência".
- mallogro has two 1911 forms. Base XXVIII: "Assim se diferençarão rêgo, substantivo, e
  rego, verbo". Base XXXIV: "pois dizemos malograr, malôgro". The noun is malôgro and the
  verb form is malogro, so the table gives mallogro its AO1990 form only.
"""
import json
from pathlib import Path

import pytest

import desacordo_ortografico
from desacordo_ortografico import convert, detect

_TABLE = Path(desacordo_ortografico.__file__).parent / "data" / "spelling.json"


def _rows(form):
    with open(_TABLE, encoding="utf-8") as f:
        return {(r["era"], r["target"]): r["value"] for r in json.load(f)["rows"] if r["form"] == form}


@pytest.mark.parametrize("text,expected", [
    ("sciencia", "sciência"),
    ("a sciencia", "a sciência"),
    ("kilo", "kilo"),
    ("um kilo de pão", "um kilo de pão"),
    ("scena", "scena"),
    ("a scena", "a scena"),
])
def test_pre_1911_text_takes_the_1911_spelling(text, expected):
    assert convert(text, "etymological", "reforma_1911") == expected


@pytest.mark.parametrize("target", ["pt_1945", "br_1943", "pt_1973", "br_1971", "ao1990-pt", "ao1990-br"])
@pytest.mark.parametrize("text,expected", [
    ("um kilo de pão", "um quilo de pão"),
    ("dois kilos de pão", "dois quilos de pão"),
])
def test_1911_kilo_takes_qu_in_later_norms(text, expected, target):
    assert convert(text, "reforma_1911", target) == expected


@pytest.mark.parametrize("target", ["pt_1945", "br_1943", "pt_1973", "br_1971", "ao1990-pt", "ao1990-br"])
@pytest.mark.parametrize("text,expected", [
    ("um kilo de pão", "um quilo de pão"),
    ("a scena", "a cena"),
    ("a sciencia", "a ciência"),
    ("o mallogro", "o malogro"),
])
def test_pre_1911_text_converts_to_later_norms(text, expected, target):
    assert convert(text, "etymological", target) == expected


def test_1911_sciencia_goes_back_to_the_pre_1911_spelling():
    assert convert("a sciência", "reforma_1911", "etymological") == "a sciencia"


@pytest.mark.parametrize("text", [
    "Comprei um kilo de arroz.",
    "A scena passa-se em Lisboa.",
    # the Formulário of 1911 itself, Base I, Excepção 2.ª
    "e tambêm na forma international kilo, que todavia se poderá escrever quilo",
])
def test_detect_reads_no_pre_1911_marker_in_a_1911_spelling(text):
    assert [m for m in detect(text).markers if m.startswith("etym")] == []


def test_detect_reads_pre_1911_sciencia_and_mallogro():
    assert "etym:sciencia" in detect("A sciencia avança.").markers
    assert "etym-pattern:mallogro" in detect("O mallogro foi grande.").markers


def test_table_rows_of_the_decided_forms():
    assert _rows("kilo") == {("reforma_1911", "pt_1945"): "quilo", ("reforma_1911", "br_1943"): "quilo"}
    assert _rows("scena") == {}
    assert _rows("sciencia") == {("etymological", "reforma_1911"): "sciência"}
    assert _rows("mallogro") == {("etymological", "ao1990-pt"): "malogro"}
