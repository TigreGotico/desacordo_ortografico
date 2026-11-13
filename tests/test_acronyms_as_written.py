"""A word in capitals converts like the same word in lowercase; an acronym stays.

AO1990 Base XIX 2º h) writes acronyms in capitals: "A letra maiúscula inicial é usada:
... h) Em siglas, símbolos ou abreviaturas internacionais ou nacionalmente reguladas com
maiúsculas, iniciais ou mediais ou finais ou o todo em maiúsculas: FAO, NATO, ONU; H2O,
Sr., V. Ex.ª." No clause exempts an acronym from the spelling rules. The rule here is
the converter's own: in mixed-case text, a token in capitals is an acronym only when its
lowercase form, diacritics aside, is no word that the converter knows (the word list or
its own word maps). Text in capitals throughout carries no such signal, so each of its
tokens converts like the same word in lowercase.
"""
import json
from pathlib import Path

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


@pytest.mark.parametrize("text, src, dst, expected", [
    # AO1990 Base XI 3º: "académico/acadêmico, anatómico/anatômico"
    ("O ESTUDO ANATÓMICO", "ao1990-pt", "ao1990-br", "O ESTUDO ANATÔMICO"),
    ("O estudo ANATÓMICO", "ao1990-pt", "ao1990-br", "O estudo ANATÔMICO"),
    # AO1990 Base XIV 1º: "aguentar"
    ("VAMOS AGÜENTAR", "pre-ao1990-br", "ao1990-br", "VAMOS AGUENTAR"),
    ("Vamos AGÜENTAR", "pre-ao1990-br", "ao1990-br", "Vamos AGUENTAR"),
    # AO1990 Base IX 3º: "assembleia, boleia, ideia"
    ("A IDÉIA", "pre-ao1990-br", "ao1990-br", "A IDEIA"),
    ("A IDÉIA dele", "pre-ao1990-br", "ao1990-br", "A IDEIA dele"),
    # AO1990 Base IV 1º b): ação
    ("A ACÇÃO foi boa.", "pt_1973", "ao1990-pt", "A AÇÃO foi boa."),
    # AO1990 Base XI 3º: António / Antônio
    ("O ANTÓNIO e o Pedro", "ao1990-pt", "ao1990-br", "O ANTÔNIO e o Pedro"),
    # Reforma de 1911: pharmacia -> farmácia
    ("O Dr. SILVA da PHARMACIA", "etymological", "pt_1973", "O Dr. SILVA da FARMÁCIA"),
])
def test_word_in_capitals_converts(text, src, dst, expected):
    assert convert(text, src, dst) == expected


def test_one_capital_letter_still_converts():
    # Reforma de 1911: pharmacia -> farmácia
    assert convert("A pharmacia", "etymological", "pt_1973") == "A farmácia"


def _gold_corpus(row_id):
    path = Path(__file__).parent.parent / "benchmark" / "gold_corpus.jsonl"
    for line in path.open(encoding="utf-8"):
        row = json.loads(line)
        if row["id"] == row_id:
            return row["cells"]
    raise KeyError(row_id)


# Rows of benchmark/gold_corpus.jsonl in capitals throughout. Their pre-1911 words (THEATRO,
# COLLECÇÃO, MAPPAS) are no listed words, and they still convert.
@pytest.mark.parametrize("row_id", ["s01", "p01-021", "p06-011"])
@pytest.mark.parametrize("target", ["pt_1973", "ao1990-pt"])
def test_text_in_capitals_converts_every_word(row_id, target):
    cells = _gold_corpus(row_id)
    assert convert(cells["etymological"].upper(), "etymological", target) == cells[target].upper()
