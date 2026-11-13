"""Pre-1911 text keeps an unaccented word that is also a modern word.

Each word below is spelled the same before and after the 1911 reform, and the
accented form next to it is a different word (Priberam lists both headwords):
pais (plural of pai) and país, continua (continuar) and contínua, antigas and
antigás, disse (dizer) and dissê, Coimbra and Coimbrã, Roma and Romã. Only the
cited 1911 word map adds a graphic accent (pharmacia -> farmácia).
"""
import pytest

from desacordo_ortografico import convert

SENTENCES = [
    "Os pais chegaram.",
    "A chuva continua.",
    "As casas antigas.",
    "Ele disse que sim.",
    "Fui a Coimbra e a Roma.",
]


@pytest.mark.parametrize("dst", ["pt_1973", "ao1990-pt", "br_1971", "ao1990-br"])
@pytest.mark.parametrize("text", SENTENCES)
def test_unaccented_modern_word_unchanged(text, dst):
    assert convert(text, "etymological", dst) == text


@pytest.mark.parametrize("dst", ["pt_1973", "ao1990-pt"])
def test_word_map_still_adds_the_1911_accent(dst):
    assert convert("A pharmacia.", "etymological", dst) == "A farmácia."
