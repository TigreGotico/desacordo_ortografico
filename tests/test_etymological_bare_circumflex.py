"""The backward pass toward etymological writes este, esse, toda, todo, fez, sobre and governo bare.

No orthographic norm governs pre-1911 print, so usage decides. In 13 pre-1911 Project Gutenberg
books (paragraph text) the bare and the accented forms count: este 1293 / êste 0, esse 1262 /
êsse 0, toda 1270 / tôda 1, todo 1064 / tôdo 0, fez 669 / fêz 0, sobre 1958 / sôbre 82, governo
211 / govêrno 15, pelo 1538 / pêlo 2 and por 5809 / pôr 143. cor / côr counts 5 / 310 and 12 of
the 13 books write the accent more often, so côr keeps it. pode / pôde counts 39 / 87: the bare
count mixes the present "pode" with the preterite, so pôde stays as the table gives it.

Eça de Queirós, Contos (Chardron, 1913, Project Gutenberg pg31347), is printed in the 1911
spelling and writes toda 124 / tôda 0, todo 116 / tôdo 0 and fez 10 / fêz 0, so the reforma_1911
target writes them bare too. The same print writes este 3 / êste 48, esse 2 / êsse 55 and sobre
5 / sôbre 233, so reforma_1911 keeps those accents.

Formulário Ortográfico de 1911, on the differential circumflex: "Assim se diferençarão rêgo,
substantivo, e rego, verbo; ... sôbre, preposição, e sobre, verbo". Formulário de 1943, 14.ª:
"fêz (s.m. e v.) e fez (s.f.)", so br_1943 keeps its accents.
"""
import json
import re
from importlib import resources

import pytest

from desacordo_ortografico import convert

NEWER = ("br_1971", "ao1990-br", "br_1943")


@pytest.mark.parametrize("source", NEWER)
@pytest.mark.parametrize("text", [
    "Este livro e esse jornal falam sobre o governo.",
    "Estes livros e esses jornais falam sobre o governo.",
    "Toda a casa e todo o povo viram o que fez.",
    "Passou pelo rio e foi por aqui.",
])
def test_the_listed_words_stay_bare_at_etymological(text, source):
    assert convert(text, source, "etymological") == text


@pytest.mark.parametrize("text, old", [
    ("Êste livro e êsse jornal falam sôbre o govêrno.", "Este livro e esse jornal falam sobre o governo."),
    ("Êstes livros e êsses jornais falam sôbre o govêrno.", "Estes livros e esses jornais falam sobre o governo."),
    ("Tôda a casa e tôdo o povo viram o que fêz.", "Toda a casa e todo o povo viram o que fez."),
    ("Fêz-se luz.", "Fez-se luz."),
])
def test_a_1943_text_goes_bare_at_etymological(text, old):
    assert convert(text, "br_1943", "etymological") == old


def test_cor_keeps_its_circumflex_and_pode_stays():
    assert convert("A cor da casa.", "br_1971", "etymological") == "A côr da casa."
    assert convert("O rei pôde vir.", "pt_1973", "etymological") == "O rei pôde vir."
    assert convert("Pôde vir.", "br_1943", "etymological") == "Pôde vir."


@pytest.mark.parametrize("source", ("br_1971", "ao1990-br"))
def test_toda_todo_and_fez_are_bare_at_reforma_1911(source):
    assert convert("Toda a casa e todo o povo viram o que fez.", source, "reforma_1911") == \
        "Toda a casa e todo o povo viram o que fez."
    assert convert("Tôda a casa e tôdo o povo viram o que fêz.", "br_1943", "reforma_1911") == \
        "Toda a casa e todo o povo viram o que fez."


@pytest.mark.parametrize("source", ("br_1971", "ao1990-br"))
def test_este_sobre_and_governo_keep_the_1911_accent(source):
    assert convert("Este livro fala sobre o governo.", source, "reforma_1911") == \
        "Êste livro fala sôbre o govêrno."


def test_br_1943_keeps_the_accents_of_its_formulario():
    assert convert("Este livro fez isso sobre o governo.", "ao1990-br", "br_1943") == \
        "Êste livro fêz isso sôbre o govêrno."


@pytest.mark.parametrize("old, new", [("êste", "este"), ("fêz", "fez"), ("govêrno", "governo")])
def test_the_forward_pass_still_drops_the_accent(old, new):
    assert convert(old, "br_1943", "br_1971") == new


def test_every_row_quotes_its_counts():
    with resources.files("desacordo_ortografico").joinpath("data/circumflex_backward.json").open(encoding="utf-8") as f:
        data = json.load(f)
    rows = [r for target in ("reforma_1911", "etymological") for r in data[target]]
    assert len(rows) == 12
    for row in rows:
        assert re.search(rf"{row['value']} \d+, {row['form']} \d+; .*{row['value']} \d+, {row['form']} \d+", row["source"]), row
