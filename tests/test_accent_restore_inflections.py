"""The 1911 accent restore leaves inflected forms alone and keeps the accent map.

The accent map gives an unaccented word its accented modern form. A word that is
itself a valid word stays as written, and so does a regular inflection of a valid
word: correu is a preterite of correr, not a bare corréu. The verb forms come from
the Dicionário Priberam conjugation tables of correr, servir, dizer, falar and ler.
The nominal forms follow Cunha & Cintra, Nova Gramática do Português Contemporâneo,
cap. 8. Context can settle some of these forms; see test_accent_guess_context.py.
"""
import json
from pathlib import Path

import pytest

from desacordo_ortografico import convert

# Bare spelling before 1911 -> modern spelling, with the AO1990 clause that accents it
ACCENTED = [
    ("agradavel", "agradável"),    # Base IX 2º a), paroxytone in -l (amável)
    ("cafe", "café"),              # Base VIII 1º a), oxytone in open -e (até, pontapé)
    ("tambem", "também"),          # Base VIII 1º c), oxytone in -em (também)
    ("liquido", "líquido"),        # Base XI 1º a), example of the clause
    ("caustico", "cáustico"),      # Base XI 1º a), example of the clause
    ("hidraulico", "hidráulico"),  # Base XI 1º a), example of the clause
]

INFLECTED = [
    "Ele disse que sim.",          # dizer, pretérito perfeito: ele disse
    "O cão correu muito.",         # correr, pretérito perfeito: ele correu
    "O rio corre ao mar.",         # correr, presente: ele corre
    "Ele servia o jantar.",        # servir, pretérito imperfeito: ele servia
    "Os filhos chegaram.",         # plural of filho
    "Subiu aos montes.",           # plural of monte
    "As casas antigas ficaram.",   # feminine plural of antigo
    "Comeu tanta fruta.",          # feminine singular of tanto
    "A febre continua alta.",      # continuar, presente: ele continua (as falar: fala)
    "O clima influencia a colheita.",  # influenciar, presente: ele influencia
    "Talvez ele cante amanhã.",    # cantar, conjuntivo: que ele cante (as falar: fale)
    "Ele leria o livro.",          # ler, condicional: ele leria
    "Assim funcionaria melhor.",   # funcionar, condicional: ele funcionaria (as falar: falaria)
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
