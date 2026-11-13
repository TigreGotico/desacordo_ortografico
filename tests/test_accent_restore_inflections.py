"""The 1911 accent restore leaves inflected forms alone and keeps the accent map.

The accent map gives an unaccented word its accented modern form. A word that is
itself a valid word stays as written, and so does a regular inflection of a valid
word: correu is a preterite of correr, not a bare corréu. The verb forms come from
the Dicionário Priberam conjugation tables of correr, servir and dizer. A bare form
whose frequent reading is the accented word keeps it: apos is após, not apo + s.
"""
import json
from pathlib import Path

import pytest

from desacordo_ortografico import convert

# Bare spelling before 1911 -> modern spelling, with the AO1990 clause that accents it
ACCENTED = [
    ("historia", "história"),      # Base XI 1º b), apparent proparoxytone in -ia (glória)
    ("agua", "água"),              # Base XI 1º b), apparent proparoxytone in -ua (língua)
    ("familia", "família"),        # Base XI 1º b), apparent proparoxytone in -ia
    ("musica", "música"),          # Base XI 1º a), proparoxytone (músico)
    ("agradavel", "agradável"),    # Base IX 2º a), paroxytone in -l (amável)
    ("cafe", "café"),              # Base VIII 1º a), oxytone in open -e (até, pontapé)
    ("tambem", "também"),          # Base VIII 1º c), oxytone in -em (também)
    ("liquido", "líquido"),        # Base XI 1º a), example of the clause
    ("caustico", "cáustico"),      # Base XI 1º a), example of the clause
    ("hidraulico", "hidráulico"),  # Base XI 1º a), example of the clause
    ("republica", "república"),    # Base XI 1º a), proparoxytone (público)
    ("pagina", "página"),          # Base XI 1º a), proparoxytone
    ("pratica", "prática"),        # Base XI 1º a), proparoxytone (plástico)
    ("avos", "avós"),              # Base VIII 1º a), lists avó(s)
    ("apos", "após"),              # Base VIII 1º a), oxytone in open -o + s (só(s))
    ("atras", "atrás"),            # Base VIII 1º a), oxytone in open -a + s (estás)
    ("viveres", "víveres"),        # Base XI 1º a), proparoxytone (Priberam: víveres)
]

INFLECTED = [
    "Ele disse que sim.",          # dizer, pretérito perfeito: ele disse
    "O cão correu muito.",         # correr, pretérito perfeito: ele correu
    "O rio corre ao mar.",         # correr, presente: ele corre
    "Ele servia o jantar.",        # servir, pretérito imperfeito: ele servia
    "Os filhos chegaram.",         # plural of filho
    "Subiu aos montes.",           # plural of monte
    "As casas antigas ficaram.",   # feminine plural of antigo
]


@pytest.mark.parametrize("bare,accented", ACCENTED)
def test_bare_word_takes_its_accent(bare, accented):
    text = convert(f"A palavra {bare} ficou.", "etymological", "pt_1973")
    assert text == f"A palavra {accented} ficou."


@pytest.mark.parametrize("text", INFLECTED)
def test_inflected_form_stays_as_written(text):
    assert convert(text, "etymological", "pt_1973") == text


def _gold_corpus(row_id):
    path = Path(__file__).parent.parent / "benchmark" / "gold_corpus.jsonl"
    for line in path.open(encoding="utf-8"):
        row = json.loads(line)
        if row["id"] == row_id:
            return row["cells"]
    raise KeyError(row_id)


@pytest.mark.parametrize("row_id", ["p02-036", "p05-034", "p06-049", "p09-024"])
def test_gold_row_keeps_the_inflected_form(row_id):
    cells = _gold_corpus(row_id)
    assert convert(cells["etymological"], "etymological", "pt_1973") == cells["pt_1973"]
