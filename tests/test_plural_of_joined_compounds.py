"""The plural of a compound that AO1990 joins is the joined plural.

Acordo Ortográfico de 1990, Base XV, 1.º Obs.: "Certos compostos, em relação aos quais se
perdeu, em certa medida, a noção de composição, grafam-se aglutinadamente: girassol,
madressilva, mandachuva, pontapé, paraquedas, paraquedista, etc." A joined noun takes the
plural -s of a word in -a, so mandachuva gives mandachuvas and paraquedista gives paraquedistas.
"""
import pytest

from desacordo_ortografico import convert
from desacordo_ortografico.lexicon import _with_plurals

PT = ("pt_1973", "ao1990-pt")
BR = ("br_1971", "ao1990-br")


@pytest.mark.parametrize("route", [PT, BR])
@pytest.mark.parametrize("word,expected", [
    ("manda-chuva", "mandachuva"),
    ("manda-chuvas", "mandachuvas"),
    ("pára-quedista", "paraquedista"),
    ("pára-quedistas", "paraquedistas"),
    ("Pára-Quedistas", "Paraquedistas"),
    ("Os pára-quedistas e os manda-chuvas.", "Os paraquedistas e os mandachuvas."),
])
def test_the_plural_joins_like_the_singular(route, word, expected):
    assert convert(word, *route) == expected


@pytest.mark.parametrize("route", [PT, BR])
@pytest.mark.parametrize("word,expected", [
    ("mandachuvas", "manda-chuvas"),
    ("paraquedistas", "pára-quedistas"),
    ("paraquedismos", "pára-quedismos"),
])
def test_the_joined_plural_goes_back_hyphenated(route, word, expected):
    assert convert(word, route[1], route[0]) == expected


@pytest.mark.parametrize("route", [PT, BR])
@pytest.mark.parametrize("word", [
    # a word in -s with no row of its singular stays as written
    "lápis", "pires", "deus", "guarda-chuvas",
    # a locution has no plural in -s (fins de semana), so no row gives one
    "fim-de-semanas", "hei-des", "dia-a-dias",
    # cor-de-rosa keeps its hyphens at AO1990
    "cor-de-rosas",
])
def test_a_word_in_s_without_a_plural_row_is_unchanged(route, word):
    assert convert(word, *route) == word


def test_a_plural_follows_the_row_of_its_singular_per_variety():
    # the pt-PT row of pára-quedismo keeps the hyphen, the pt-BR row joins
    assert convert("pára-quedismos", *PT) == "para-quedismos"
    assert convert("pára-quedismos", *BR) == "paraquedismos"


def test_foto_receptores_keeps_its_p_toward_pt_br():
    # foto-receptor drops the p toward pt-PT only; the VOLP keeps it in pt-BR
    assert convert("foto-receptores", "pt_1973", "ao1990-br") == "fotorreceptores"


def test_only_a_row_that_joins_or_drops_an_accent_gets_a_plural_row():
    rows = {"manda-chuva": "mandachuva", "pêra": "pera", "recta": "reta",
            "fim-de-semana": "fim de semana"}
    assert _with_plurals(rows) == {**rows, "manda-chuvas": "mandachuvas", "pêras": "peras"}
