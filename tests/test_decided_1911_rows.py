"""The pre-1911 rows that the Formulário Ortográfico of 1911 decides.

Each expected form comes from a clause, not from the converter:

- kilo keeps its pre-1911 row kilo -> quilo. Base I, Excepção 2.ª permits kilo, and writes
  quilo as the better form: "Continuam em uso os símbolos W, para denotar o Oeste, e K como
  abreviatura de unidade métrica, e tambêm na forma international kilo, que todavia se
  poderá escrever quilo; tanto mais, que o k é um grosseiro êrro nesta palavra, pois o
  correspondente termo grego se escreve com χ, e não κ." quilo is also the only 1911
  spelling of the chyle, pre-1911 chylo. So the 1911 form to write is quilo.
- scena and sciência are 1911 spellings. Base XI: "É conservado o grupo inicial sc, das
  seguintes palavras e seus derivados e afins, em que o s é mudo: scena, sciência, scetro".
  1943, 19.: "Elimina-se o s do grupo inicial sc: celerado, cena, cenografia, ciência".
- Going back from a later norm, cena gives scena and ciência gives sciência, so an
  etymological target gets scena and sciencia. quilo stays quilo in 1911. The initial-sc
  rule stays one-way, because its inverse would give scenoura from cenoura: rows of the
  edges out of 1911 carry the backward fact.
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
    ("scena", "scena"),
    ("a scena", "a scena"),
])
def test_pre_1911_text_takes_the_1911_spelling(text, expected):
    assert convert(text, "etymological", "reforma_1911") == expected


@pytest.mark.parametrize("text,expected", [
    ("kilo", "quilo"),
    ("um kilo de pão", "um quilo de pão"),
])
def test_pre_1911_kilo_takes_the_1911_quilo(text, expected):
    assert convert(text, "etymological", "reforma_1911") == expected


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
    "A scena passa-se em Lisboa.",
    "O director de scena ajustou as luzes.",
])
def test_detect_reads_no_pre_1911_marker_in_a_1911_spelling(text):
    assert [m for m in detect(text).markers if m.startswith("etym")] == []


def test_detect_reads_pre_1911_sciencia_and_mallogro():
    assert "etym:sciencia" in detect("A sciencia avança.").markers
    assert "etym-pattern:mallogro" in detect("O mallogro foi grande.").markers


def test_table_rows_of_the_decided_forms():
    assert _rows("kilo") == {("etymological", "reforma_1911"): "quilo"}
    rows_1911 = {("reforma_1911", "pt_1945"): "cena", ("reforma_1911", "br_1943"): "cena"}
    assert _rows("scena") == rows_1911
    assert _rows("sciência") == {k: "ciência" for k in rows_1911}
    assert _rows("sciencia") == {("etymological", "reforma_1911"): "sciência"}
    assert _rows("mallogro") == {("etymological", "ao1990-pt"): "malogro"}


_LATER = ["pt_1945", "br_1943", "pt_1973", "br_1971", "ao1990-pt", "ao1990-br"]


@pytest.mark.parametrize("source", _LATER)
@pytest.mark.parametrize("text,in_1911,pre_1911", [
    ("a cena", "a scena", "a scena"),
    ("a ciência", "a sciência", "a sciencia"),
    ("Ciência", "Sciência", "Sciencia"),
])
def test_later_text_goes_back_to_1911_and_before(text, in_1911, pre_1911, source):
    assert convert(text, source, "reforma_1911") == in_1911
    assert convert(text, source, "etymological") == pre_1911


@pytest.mark.parametrize("source", _LATER)
@pytest.mark.parametrize("text", ["dois quilos", "as cenas", "as ciências"])
def test_backward_rows_read_no_plural(text, source):
    # as the backward 1911 pass: sciências would be a 1911-only form at an etymological
    # target, because that pass reads no plural either
    assert convert(text, source, "reforma_1911") == text
    assert convert(text, source, "etymological") == text


@pytest.mark.parametrize("source", _LATER)
def test_later_quilo_stays_quilo_in_1911(source):
    # quilo is the 1911 form of the kilogram and the only 1911 form of the chyle (chylo).
    # An etymological target gets kilo from the curated pre-1911 row kilo -> quilo.
    assert _rows("chylo") == {("etymological", "reforma_1911"): "quilo"}
    assert convert("um quilo de pão", source, "reforma_1911") == "um quilo de pão"
    assert convert("um quilo de pão", source, "etymological") == "um kilo de pão"


@pytest.mark.parametrize("source", _LATER)
@pytest.mark.parametrize("text", ["a cenoura", "o cenáculo", "a celeridade", "quase", "tão", "também"])
def test_backward_rows_leave_other_words_as_written(text, source):
    # no rule goes backward: these words have no curated row out of 1911
    assert convert(text, source, "reforma_1911") == text
