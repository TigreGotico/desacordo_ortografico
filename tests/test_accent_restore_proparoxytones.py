"""The 1911 accent restore adds only the accent of a proparoxytone.

AO1990 Base XI accents every proparoxytone, real or apparent ("barbárie, série"), so an
unaccented old spelling of one is no modern word: fosforo is fósforo. An unaccented
paroxytone or oxytone is a valid modern spelling (Base X 2º: "Aboim, Coimbra, ruim"),
and the word list lacks most inflected forms, so the converter leaves it as written.
The gold rows are rows of gold_full.jsonl (Hugging Face dataset
TigreGotico/desacordo_ortografico).
"""
import pytest

from desacordo_ortografico import convert


def modern(text):
    return convert(text, "etymological", "pt_1973")


@pytest.mark.parametrize("text", [
    "Ele disse que sim.",                  # the pt_1973 gold cells write disse
    "Vive em Coimbra. Coimbra é linda.",   # Base X 2º: Coimbra
    "A chuva continua.",                   # the pt_1973 gold cells write continua
    "As casas antigas.",                   # the pt_1973 gold cells write antigas
    "Os pais dele.",                       # the pt_1973 gold cells write pais
    "Ele integra a equipa.",               # integrar; the gold cells write integra
])
def test_unaccented_word_stays(text):
    assert modern(text) == text


@pytest.mark.parametrize("old, new", [
    ("fosforo", "fósforo"),        # Base XI 1º a: proparoxytone
    ("geofisica", "geofísica"),    # gold pt_1973 cells
    ("analitica", "analítica"),    # gold pt_1973 cells
    ("serie", "série"),            # Base XI 1º b: "barbárie, série"
])
def test_proparoxytone_takes_its_accent(old, new):
    assert modern(f"a {old}") == f"a {new}"
