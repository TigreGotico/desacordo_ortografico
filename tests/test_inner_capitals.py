"""A word with a capital inside it is a symbol or a name, and it stays as written.

AO1990 Base XIX 2º h) writes symbols and acronyms "com maiúsculas, iniciais ou mediais
ou finais ou o todo em maiúsculas: FAO, NATO, ONU; H2O, Sr., V. Ex.ª", and Base I 2º c)
lists the symbol kW. The converter re-applies one of three case patterns to a word:
lowercase, initial capital, or capitals throughout. A word with a capital after its
first letter fits none of them, so the converter leaves it as written.

A compound takes the case of each hyphen or apostrophe segment. When the segments join,
the result takes the case of the first segment: AO1990 Base XVI 2º a) and b) join
"antirreligioso, antissemita, contrarregra" and "autoestrada".
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
]


@pytest.mark.parametrize("src, dst", PATHS)
@pytest.mark.parametrize("word", WORDS)
def test_word_with_an_inner_capital_stays_as_written(src, dst, word):
    assert convert(f"Viu o {word} ontem.", src, dst) == f"Viu o {word} ontem."


@pytest.mark.parametrize("text, src, dst, expected", [
    ("Anti-Semitismo", "pre-ao1990-pt", "ao1990-pt", "Antissemitismo"),  # Base XVI 2º b)
    ("Auto-Estrada", "pre-ao1990-pt", "ao1990-pt", "Autoestrada"),       # Base XVI 2º a)
    ("Contra-Regra", "pre-ao1990-pt", "ao1990-pt", "Contrarregra"),      # Base XVI 2º b)
    ("Ultra-Som", "pre-ao1990-br", "ao1990-br", "Ultrassom"),            # Base XVI 2º b)
])
def test_joined_compound_takes_the_case_of_its_first_segment(text, src, dst, expected):
    assert convert(text, src, dst) == expected


@pytest.mark.parametrize("text, src, dst, expected", [
    ("Vive em Trás-os-Montes.", "pre-ao1990-pt", "ao1990-pt", "Vive em Trás-os-Montes."),
    ("Vive na Guiné-Bissau.", "pre-ao1990-pt", "ao1990-pt", "Vive na Guiné-Bissau."),
    ("Nasceu em Castello-Branco.", "etymological", "pt_1973", "Nasceu em Castelo-Branco."),
    ("A romaria de São João d'Arga.", "pre-ao1990-pt", "ao1990-pt",
     "A romaria de São João d'Arga."),
])
def test_compound_keeps_the_case_of_each_segment(text, src, dst, expected):
    assert convert(text, src, dst) == expected


@pytest.mark.parametrize("text, expected", [("A Pharmacia.", "A Farmácia."),
                                             ("A PHARMACIA.", "A FARMÁCIA.")])
def test_initial_capital_and_capitals_throughout_still_convert(text, expected):
    # The other two case patterns: the word converts and keeps its pattern.
    assert convert(text, "etymological", "pt_1973") == expected
