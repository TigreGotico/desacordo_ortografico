"""A br_1971 row of the spelling table has a key that Brazil wrote before the AO1990.

The inverse of a br_1971 row is the backward map toward br_1971. Three tugalex rows had a
key that no Brazilian norm wrote, so the backward map gave it:

- ABL, Pequeno Vocabulário Ortográfico da Língua Portuguesa (1943): "co-diretor, s. m.", so
  Brazil wrote co-diretora, with no c, before the AO1990. The vocabulary lists the lemma
  only; the plural of a noun in -or and of a noun in -a is regular, so Brazil wrote
  co-diretores and co-diretoras.
- The same vocabulary writes the family of eletricidade without the c ("eletricidade, s. f.",
  "dielétrico, adj. e s. m.", "idieletricidade, s. f."), and the ABL VOLP lists
  zoeletricidade s.f. and dieletricidade s.f. with no form with a c. No source gives a
  Brazilian zoelectricidade or dielectricidade, so zoeletricidade and dieletricidade stay as
  written.
"""
import pytest

from desacordo_ortografico import convert


@pytest.mark.parametrize("text, source, expected", [
    ("codiretora", "ao1990-br", "co-diretora"),
    ("codiretora", "ao1990-pt", "co-diretora"),
    ("co-directora", "pt_1973", "co-diretora"),
    ("codiretores", "ao1990-br", "co-diretores"),
    ("codiretoras", "ao1990-pt", "co-diretoras"),
    ("co-directores", "pt_1973", "co-diretores"),
    ("co-directoras", "pt_1973", "co-diretoras"),
    ("zoeletricidade", "ao1990-br", "zoeletricidade"),
    ("zoelectricidade", "pt_1973", "zoeletricidade"),
    ("dieletricidade", "ao1990-br", "dieletricidade"),
    ("dieletricidade", "ao1990-pt", "dieletricidade"),
])
def test_br_1971_gets_the_1943_form(text, source, expected):
    assert convert(text, source, "br_1971") == expected


def test_co_diretora_joins_at_ao1990():
    assert convert("a co-diretora", "br_1971", "ao1990-br") == "a codiretora"


def test_co_diretores_join_at_ao1990():
    assert convert("os co-diretores e as co-diretoras", "br_1971", "ao1990-br") == "os codiretores e as codiretoras"
