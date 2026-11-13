"""A word in capitals throughout keeps its word-map lookups and skips the rule fallbacks.

AO1990 Base XIX 2º h) writes acronyms in capitals: "A letra maiúscula inicial é usada:
... h) Em siglas, símbolos ou abreviaturas internacionais ou nacionalmente reguladas com
maiúsculas, iniciais ou mediais ou finais ou o todo em maiúsculas: FAO, NATO, ONU; H2O,
Sr., V. Ex.ª." No clause exempts an acronym from the spelling rules. The rule here is
the converter's own: a word in capitals may be an acronym, which is a string of letters
and not a word, so a rule fallback must not rewrite it. A word that a word map holds is
a word, and converts.
"""
import pytest

from desacordo_ortografico import convert


# IPTU, the Brazilian urban property tax, loses its p to the silent c/p rule.
# PPD, the Partido Popular Democrático, loses a p to the 1911 geminate rule.
@pytest.mark.parametrize("text, src, dst", [
    ("Pagou o IPTU.", "pre-ao1990-pt", "ao1990-pt"),
    ("Pagou o IPTU.", "pt_1973", "ao1990-br"),
    ("Votou no PPD.", "etymological", "pt_1973"),
])
def test_acronym_stays(text, src, dst):
    assert convert(text, src, dst) == text


def test_acronym_in_text_in_capitals_stays():
    assert convert("PAGOU O IPTU.", "pre-ao1990-pt", "ao1990-pt") == "PAGOU O IPTU."


@pytest.mark.parametrize("text, src, dst, expected", [
    # AO1990 Base XI 3º: António / Antônio
    ("O ANTÓNIO e o Pedro", "ao1990-pt", "ao1990-br", "O ANTÔNIO e o Pedro"),
    # AO1990 Base IV 1º b): ação
    ("A ACÇÃO foi boa.", "pt_1973", "ao1990-pt", "A AÇÃO foi boa."),
    # Reforma de 1911: pharmacia -> farmácia
    ("O Dr. SILVA da PHARMACIA", "etymological", "pt_1973", "O Dr. SILVA da FARMÁCIA"),
])
def test_word_in_capitals_keeps_its_word_map(text, src, dst, expected):
    assert convert(text, src, dst) == expected


def test_one_capital_letter_still_converts():
    # Reforma de 1911: pharmacia -> farmácia
    assert convert("A pharmacia", "etymological", "pt_1973") == "A farmácia"
