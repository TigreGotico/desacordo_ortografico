"""Four prefix compounds and euro-região join at AO1990.

AO1990 Base XVI 1: "Nas formações com prefixos (como, por exemplo: ante-, anti-, circum-,
co-, contra-, entre-, extra-, ... ) e em formações por recomposição ... de origem grega e
latina (tais como: aero-, agro-, arqui-, auto-, bio-, eletro-, ... mini-, multi-, ... ), só se
emprega o hífen nos seguintes casos", and none of cases a) to f) (h, the same vowel, circum-
and pan-, hiper-, inter- and super- before r, ex-, sota-, soto-, vice- and vizo-, pós-, pré-
and pró-) applies to anti-tabaco, auto-defesa, mini-golfe or entre-ajuda.

The VOP (Portal da Língua Portuguesa) lists "antitabaco - adjetivo" (lemma 118408),
"autodefesa - nome feminino" (54891), "minigolfe - nome masculino" (113443) and "entreajuda -
nome feminino" (61692). The VOLP lists "antitabaco adj.2g.2n." and "autodefesa (ê) s.f.", and has
no entry for minigolfe or entreajuda.

Base XVI 2.º a): "Nas formações em que o prefixo ou falso prefixo termina em vogal e o segundo
elemento começa por r ou s, devendo estas consoantes duplicar-se". The VOP lists "eurodeputado -
nome masculino" (lemma 1635), and the VOLP "eurodeputado s.m." and "eurocomunismo s.m.", so euro-
joins a noun. Neither vocabulary lists euro-região or eurorregião. The hyphen of euro-africano
and euro-siberiano (VOLP) belongs to compounds of two adjectives (Base XV 1) and stays.
"""
import pytest

from desacordo_ortografico import convert

PT = ("pt_1973", "ao1990-pt")
BR = ("br_1971", "ao1990-br")


@pytest.mark.parametrize("old, new", [
    ("A lei anti-tabaco entrou em vigor.", "A lei antitabaco entrou em vigor."),
    ("Ensinou a auto-defesa às alunas.", "Ensinou a autodefesa às alunas."),
    ("Jogámos mini-golfe no domingo.", "Jogámos minigolfe no domingo."),
    ("A entre-ajuda dos vizinhos é antiga.", "A entreajuda dos vizinhos é antiga."),
    ("As auto-defesas das aldeias.", "As autodefesas das aldeias."),
])
def test_the_hyphen_goes_toward_pt_pt(old, new):
    assert convert(old, *PT) == new


@pytest.mark.parametrize("old, new", [
    ("A lei anti-tabaco entrou em vigor.", "A lei antitabaco entrou em vigor."),
    ("Ensinou a auto-defesa às alunas.", "Ensinou a autodefesa às alunas."),
])
def test_the_hyphen_goes_toward_pt_br(old, new):
    assert convert(old, *BR) == new


@pytest.mark.parametrize("old, new", [
    ("A lei antitabaco entrou em vigor.", "A lei anti-tabaco entrou em vigor."),
    ("Ensinou a autodefesa às alunas.", "Ensinou a auto-defesa às alunas."),
])
@pytest.mark.parametrize("source, target", [("ao1990-pt", "pt_1973"), ("ao1990-br", "br_1971")])
def test_the_pre_1990_norm_writes_the_hyphen(old, new, source, target):
    assert convert(old, source, target) == new


@pytest.mark.parametrize("source, target", [PT, BR])
@pytest.mark.parametrize("old, new", [
    ("A euro-região do norte.", "A eurorregião do norte."),
    ("As euro-regiões do norte.", "As eurorregiões do norte."),
])
def test_euro_joins_a_noun_that_starts_with_r(old, new, source, target):
    assert convert(old, source, target) == new


def test_euro_region_goes_back_with_its_hyphen():
    assert convert("As eurorregiões do norte.", "ao1990-pt", "pt_1973") == "As euro-regiões do norte."


@pytest.mark.parametrize("source, target", [PT, BR])
@pytest.mark.parametrize("text", ["O euro-siberiano e o euro-africano.", "Um eurodeputado do norte."])
def test_a_euro_compound_of_two_adjectives_and_a_joined_word_stay(text, source, target):
    assert convert(text, source, target) == text
