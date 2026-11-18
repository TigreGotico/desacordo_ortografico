"""br_1971 and ao1990-br -> br_1943: the backward 1971 map gives the 1943 circumflex back.

The 1943 Formulário, 14.ª, writes the differential circumflex on the closed e or o of a
word that is a homograph of a word with the open vowel: "sôbre (prep.) e sobre (v.)",
"fêz (s.m. e v.) e fez (s.f.)", "êle", "aquêles", "dêles". Lei n.º 5.765/1971, Art. 1.º,
abolished it, so a route back to br_1943 restores it. The map holds no row for a word whose
bare form is the more frequent reading (corte, deveras, colher), desacordo#70.
"""
import pytest

from desacordo_ortografico import convert

SOURCES = ("br_1971", "ao1990-br")


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("bare,accented", [
    ("sobre", "sôbre"),
    ("fez", "fêz"),
    ("ele", "êle"),
    ("aqueles", "aquêles"),
    ("deles", "dêles"),
])
def test_the_1943_circumflex_comes_back(bare, accented, source):
    assert convert(bare, source, "br_1943") == accented


@pytest.mark.parametrize("source", SOURCES)
def test_a_word_left_out_of_the_map_stays(source):
    assert convert("corte", source, "br_1943") == "corte"


def test_sentence():
    assert convert("Sobre eles, fez o que pôde.", "ao1990-br", "br_1943") == \
        "Sôbre êles, fêz o que pôde."
