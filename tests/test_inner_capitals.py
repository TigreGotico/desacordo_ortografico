"""A word with a capital inside it is a symbol or a name, and it stays as written.

AO1990 Base XIX 2º h) writes symbols and acronyms "com maiúsculas, iniciais ou mediais
ou finais ou o todo em maiúsculas: FAO, NATO, ONU; H2O, Sr., V. Ex.ª", and Base I 2º c)
lists the symbol kW. The converter re-applies one of three case patterns to a word:
lowercase, initial capital, or capitals throughout. A word with a capital after its
first letter fits none of them, so the converter leaves it as written.
"""
import pytest

from desacordo_ortografico import convert

PATHS = [("etymological", "pt_1973"), ("pre-ao1990-pt", "ao1990-pt"),
         ("pre-ao1990-br", "ao1990-br")]

WORDS = [
    "pH",            # symbol, final capital (Base XIX 2º h)
    "kW",            # symbol, Base I 2º c): kW-kilowatt
    "McDonald",      # foreign name, medial capital
    "iPhone",        # trade name, medial capital
    "PhD",           # abbreviation, initial and final capitals
    "TVs",           # plural of an acronym
    "Guiné-Bissau",  # place name, a capital after the hyphen
]


@pytest.mark.parametrize("src, dst", PATHS)
@pytest.mark.parametrize("word", WORDS)
def test_word_with_an_inner_capital_stays_as_written(src, dst, word):
    assert convert(f"Viu o {word} ontem.", src, dst) == f"Viu o {word} ontem."


@pytest.mark.parametrize("text, expected", [("A Pharmacia.", "A Farmácia."),
                                             ("A PHARMACIA.", "A FARMÁCIA.")])
def test_initial_capital_and_capitals_throughout_still_convert(text, expected):
    # The other two case patterns: the word converts and keeps its pattern.
    assert convert(text, "etymological", "pt_1973") == expected
