"""The AO1990 forms para-quedas, para-quedista and para-quedismo take the accent of pára
back toward every norm before AO1990.

Inside the compound, para is the verb, never the preposition. The Acordo Ortográfico de
1945 writes "pára-quedas", and its derivatives "pára-quedista [...] em harmonia com [...]
pára-quedas". ABL, Pequeno Vocabulário Ortográfico (1943): "pára-quedas, s. m. 2 núm.",
"pára-quedista, s. 2 gên.".
"""
import pytest

from desacordo_ortografico import convert

OLDER = ("etymological", "reforma_1911", "pt_1945", "pt_1973", "br_1943", "br_1971")

WORDS = [
    ("para-quedas", "pára-quedas"),
    ("para-quedista", "pára-quedista"),
    ("para-quedistas", "pára-quedistas"),
    ("para-quedismo", "pára-quedismo"),
]


@pytest.mark.parametrize("target", OLDER)
@pytest.mark.parametrize("source", ("ao1990-pt", "ao1990-br"))
@pytest.mark.parametrize("word,accented", WORDS)
def test_the_accent_comes_back(word, accented, source, target):
    assert convert(word, source, target) == accented


@pytest.mark.parametrize("target", ("pt_1973", "br_1971"))
def test_sentence(target):
    text = "O para-quedista abriu o para-quedas."
    assert convert(text, "ao1990-pt", target) == "O pára-quedista abriu o pára-quedas."
