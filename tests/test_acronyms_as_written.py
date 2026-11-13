"""In mixed-case text, a word in capitals throughout stays as written.

AO1990 Base I 2º c), the clause on k, w and y, writes acronyms as they are ("Em siglas,
símbolos ...: TWA, KLM"). A word in capitals inside mixed-case text may be an acronym (IPTU, the Brazilian
urban property tax), and the spelling alone cannot tell an acronym from a word, so it stays.
Text in capitals throughout (a heading) is words, and converts.
"""
import pytest

from desacordo_ortografico import convert


@pytest.mark.parametrize("src, dst", [("pre-ao1990-pt", "ao1990-pt"),
                                      ("pre-ao1990-br", "ao1990-br"),
                                      ("etymological", "pt_1973")])
def test_acronym_stays(src, dst):
    assert convert("Pagou o IPTU.", src, dst) == "Pagou o IPTU."


def test_one_capital_letter_still_converts():
    # Reforma de 1911: pharmacia -> farmácia
    assert convert("A pharmacia", "etymological", "pt_1973") == "A farmácia"


def test_text_in_capitals_still_converts():
    # Reforma de 1911: pharmacia -> farmácia
    assert convert("A PHARMACIA", "etymological", "pt_1973") == "A FARMÁCIA"
