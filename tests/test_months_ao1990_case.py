"""AO1990 Base XIX 1º: "A letra minúscula inicial é usada: ... b) Nos nomes dos dias,
meses, estações do ano: segunda-feira; outubro; primavera."

So a conversion toward AO1990 lowers a month or season name mid-sentence and never
raises a lowercase one. A capital that opens a sentence stays.
"""
import pytest

from desacordo_ortografico import convert

PATHS = [("pre-ao1990-br", "ao1990-br"), ("pre-ao1990-pt", "ao1990-pt")]


@pytest.mark.parametrize("src, dst", PATHS)
@pytest.mark.parametrize("word", ["janeiro", "outubro", "primavera"])
def test_lowercase_name_stays_lowercase(src, dst, word):
    assert convert(word, src, dst) == word


@pytest.mark.parametrize("src, dst", PATHS)
def test_capital_mid_sentence_is_lowered(src, dst):
    assert convert("Chegou em Outubro.", src, dst) == "Chegou em outubro."


@pytest.mark.parametrize("src, dst", PATHS)
def test_capital_opening_a_sentence_stays(src, dst):
    assert convert("Outubro chegou.", src, dst) == "Outubro chegou."
