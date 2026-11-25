"""destróier keeps its accent at AO1990.

VOLP (ABL): "destróier s.m."; a search for "destroier" returns "destróier s.m.". The Pequeno
Vocabulário Ortográfico da Língua Portuguesa of 1943, scan page 522: "destróier, s. m.: adapt.
do ingl. destroyer." Priberam heads the entry "destróier", marked "[Brasil] [Marinha]", with no
AO1990 change. The VOP has no entry for either spelling.

AO1990 Base IX 3 takes the accent off the diphthongs ei and oi of paroxytones (ideia, heroico,
jiboia), and the word follows the vocabularies, not that rule.
"""
import pytest

from desacordo_ortografico import convert

ROUTES = [
    ("br_1971", "ao1990-br"), ("br_1943", "ao1990-br"), ("pt_1973", "ao1990-br"),
    ("pt_1973", "ao1990-pt"), ("pt_1945", "ao1990-pt"), ("etymological", "ao1990-pt"),
    ("ao1990-br", "br_1971"), ("ao1990-pt", "pt_1973"),
]


@pytest.mark.parametrize("source, target", ROUTES)
@pytest.mark.parametrize("text", [
    "O destróier atracou no porto.",
    "O Destróier atracou no porto.",
    "O DESTRÓIER ATRACOU NO PORTO.",
    "Os destróieres atracaram no porto.",
    "O contratorpedeiro-destróier atracou no porto.",
])
def test_destroier_keeps_its_accent(text, source, target):
    assert convert(text, source, target) == text


def test_the_other_oi_and_ei_paroxytones_still_lose_the_accent():
    assert convert("A idéia heróica do destróier.", "br_1943", "ao1990-br") == "A ideia heroica do destróier."
