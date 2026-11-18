"""AO1990 writes no hyphen between a monosyllabic present form of haver and de.

AO1990, Base XVII, 2.º: "Não se emprega o hífen nas ligações da preposição de às formas
monossilábicas do presente do indicativo do verbo haver: hei de, hás de, hão de, etc."
The monosyllabic forms are hei, hás, há, heis and hão.
"""
import pytest

from desacordo_ortografico import convert

ROUTES = [
    ("etymological", "ao1990-pt"),
    ("etymological", "ao1990-br"),
    ("pt_1973", "ao1990-pt"),
    ("pt_1973", "ao1990-br"),
]

FORMS = [
    ("hei-de", "hei de"),
    ("hás-de", "hás de"),
    ("há-de", "há de"),
    ("heis-de", "heis de"),
    ("hão-de", "hão de"),
]


@pytest.mark.parametrize("src,dst", ROUTES)
@pytest.mark.parametrize("word,joined", FORMS)
def test_haver_de_drops_the_hyphen(word, joined, src, dst):
    assert convert(word, src, dst) == joined


@pytest.mark.parametrize("src,dst", ROUTES)
def test_sentence(src, dst):
    assert convert("Hei-de voltar, e tu hás-de ver.", src, dst) == "Hei de voltar, e tu hás de ver."
