"""Words that the pre-1990 norms already wrote joined stay joined, and euro-região joins at pt-BR.

The prefixes auto-, anti- and entre- take the hyphen before a consonant in no pre-1990 norm.
Acordo Ortográfico de 1945, Base XXIX (Bases Analíticas 29), 2.º: "compostos formados com os
elementos de origem grega auto, neo, proto e pseudo, quando o segundo elemento tem vida à
parte e começa por vogal, h, r ou s"; 3.º: "compostos formados com os prefixos anti, arqui e
semi, quando o segundo elemento tem vida à parte e começa por h, i, r ou s"; 4.º: "compostos
formados com os prefixos ante, entre e sobre, quando o segundo elemento tem vida à parte e
começa por h". Formulário Ortográfico de 1943, 46, 5.º a): "auto, contra, extra, ... semi e
ultra, quando se lhes seguem palavras começadas por vogal, h, r ou s", and b): "ante, anti,
arqui e sôbre, quando seguidos de palavras iniciadas por h, r ou s". So autodefesa,
antitabaco and entreajuda were joined before 1990, and the backward route must not write a
hyphen. Neither text lists mini- or euro- in those clauses, so minigolfe has no row.

AO1990 Base XVI 1 and the VOP ("antitabaco - adjetivo", lemma 118408; "autodefesa - nome
feminino", 54891; "minigolfe - nome masculino", 113443; "entreajuda - nome feminino", 61692)
agree with the joined forms.

Formulário de 1943, 46, 3.º Observação, keeps euro (=europeu) with a hyphen: "euro-africano".
Base XVI 2.º a) doubles the r after a vowel prefix, and the VOP lists "eurodeputado - nome
masculino" (lemma 1635) and the VOLP "eurodeputado s.m." and "eurocomunismo s.m.". No
vocabulary lists euro-região or eurorregião. The 1945 text has no clause for euro-, so the
pt-PT side has no row. The hyphen of euro-africano and euro-siberiano (VOLP) belongs to
compounds of two adjectives (Base XV 1) and stays.
"""
import pytest

from desacordo_ortografico import convert

JOINED = [
    ("A lei antitabaco entrou em vigor.", "ao1990-pt"),
    ("Ensinou a autodefesa às alunas.", "ao1990-pt"),
    ("Jogámos minigolfe no domingo.", "ao1990-pt"),
    ("A entreajuda dos vizinhos é antiga.", "ao1990-pt"),
    ("A lei antitabaco entrou em vigor.", "ao1990-br"),
    ("Ensinou a autodefesa às alunas.", "ao1990-br"),
]


@pytest.mark.parametrize("text, source", JOINED)
@pytest.mark.parametrize("target", ["pt_1973", "pt_1945", "br_1971", "br_1943", "reforma_1911", "etymological"])
def test_a_word_that_the_old_norms_wrote_joined_stays_joined_going_back(text, source, target):
    word = next(w for w in ("antitabaco", "autodefesa", "minigolfe", "entreajuda") if w in text)
    assert word in convert(text, source, target)


@pytest.mark.parametrize("text", [
    "A lei antitabaco entrou em vigor.",
    "Ensinou a autodefesa às alunas.",
    "A entreajuda dos vizinhos é antiga.",
])
def test_a_joined_word_stays_joined_at_both_ao1990_norms(text):
    for source, target in (("ao1990-pt", "ao1990-br"), ("ao1990-br", "ao1990-pt"), ("pt_1973", "ao1990-pt")):
        assert convert(text, source, target) == text


@pytest.mark.parametrize("old, new", [
    ("A euro-região do norte.", "A eurorregião do norte."),
    ("As euro-regiões do norte.", "As eurorregiões do norte."),
])
def test_euro_joins_a_noun_that_starts_with_r_at_pt_br(old, new):
    assert convert(old, "br_1971", "ao1990-br") == new


def test_euro_region_goes_back_with_its_hyphen_at_br_1971():
    assert convert("As eurorregiões do norte.", "ao1990-br", "br_1971") == "As euro-regiões do norte."


@pytest.mark.parametrize("source, target", [("pt_1973", "ao1990-pt"), ("br_1971", "ao1990-br")])
@pytest.mark.parametrize("text", ["O euro-siberiano e o euro-africano.", "Um eurodeputado do norte."])
def test_a_euro_compound_of_two_adjectives_and_a_joined_word_stay(text, source, target):
    assert convert(text, source, target) == text
