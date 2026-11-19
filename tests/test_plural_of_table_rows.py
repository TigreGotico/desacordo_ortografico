"""The plural of a word that a spelling-table row holds follows the row.

Each expected value is the singular's own row plus the regular plural of Portuguese: a word
in -a, -e or -o takes -s (antirracista, antirracistas), a word in -z or -or takes -es
(atriz, atrizes; coautor, coautores), -al makes -ais and -vel makes -eis. The Acordo de 1945,
Base XXII, names the one irregular case: "pêra, substantivo, e pera, preposição arcaica (mas
o plural, peras, sem acento)". So peras keeps its form toward every older norm.
"""
import pytest

from desacordo_ortografico import convert

PT = ("ao1990-pt", "pt_1973")
BR = ("ao1990-br", "br_1971")


@pytest.mark.parametrize("word,route,expected", [
    # anti-racista -> antirracista, auto-escola -> autoescola (joined at AO1990)
    ("antirracistas", PT, "anti-racistas"),
    ("autoescolas", PT, "auto-escolas"),
    ("autoescolas", BR, "auto-escolas"),
    # agro-industrial -> agroindustrial, auto-sustentável -> autossustentável
    ("agroindustriais", PT, "agro-industriais"),
    ("autossustentáveis", PT, "auto-sustentáveis"),
    # idéia -> ideia, heróico -> heroico, alcalóide -> alcaloide (accent dropped at AO1990)
    ("ideias", BR, "idéias"),
    ("heroicos", BR, "heróicos"),
    ("alcaloides", BR, "alcalóides"),
    # co-diretor -> codiretor, co-diretora -> codiretora (Brazilian rows)
    ("codiretores", BR, "co-diretores"),
    ("codiretoras", BR, "co-diretoras"),
    # coautor -> co-autor, actriz -> atriz
    ("coautores", PT, "co-autores"),
    ("atrizes", PT, "actrizes"),
])
def test_the_plural_of_a_row_goes_back_with_its_singular(word, route, expected):
    assert convert(word, *route) == expected


@pytest.mark.parametrize("word,expected", [
    # actor-encenador -> ator-encenador, actriz -> atriz, afectador -> afetador
    ("actores-encenadores", "atores-encenadores"),
    ("actrizes", "atrizes"),
    ("afectadores", "afetadores"),
])
def test_the_plural_of_a_row_goes_forward_with_its_singular(word, expected):
    assert convert(word, "pt_1973", "ao1990-pt") == expected


@pytest.mark.parametrize("word,route", [
    # pera is a row that gives pêra, and its plural never took the accent
    ("peras", PT), ("peras", BR),
    # pelo, polo, trato: the bare form is another word, so no row gives the old form
    ("pelos", PT), ("tratos", PT), ("contratos", PT), ("retratos", PT),
    # corretor (a broker), edital and retor (a teacher of rhetoric) are words of their own
    # with one spelling (Priberam)
    ("corretores", PT), ("editais", PT), ("retores", PT),
    ("os corretores de seguros", PT),
    # no row holds the singular
    ("cadeiras", PT), ("cadeiras", BR), ("casas", PT), ("pares", PT),
])
def test_a_plural_without_a_row_for_its_singular_stays(word, route):
    assert convert(word, *route) == word


@pytest.mark.parametrize("singular,route,expected", [
    ("antirracista", PT, "anti-racista"), ("autoescola", PT, "auto-escola"),
    ("ideia", BR, "idéia"), ("heroico", BR, "heróico"), ("alcaloide", BR, "alcalóide"),
    ("codiretor", BR, "co-diretor"), ("coautor", PT, "co-autor"), ("atriz", PT, "actriz"),
])
def test_the_singular_rows_behind_the_plurals(singular, route, expected):
    assert convert(singular, *route) == expected
