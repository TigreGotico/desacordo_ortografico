"""br_1971 drops the differential circumflex of the 1943 Formulário, 14.ª.

Lei n.º 5.765, de 18 de dezembro de 1971, Art. 1.º: "fica abolido o trema nos hiatos
átonos; o acento circunflexo diferencial na letra e e na letra o, a sílaba tônica das
palavras homógrafas de outras em que são abertas a letra e e a letra o, exceção feita
da forma pôde, que se acentuará por oposição a pode".

The words are the ones that the 1943 Formulário names for that accent, 14.ª:
"Emprega-se o acento circunflexo como diferencial ou distintivo no e e no o fechados da
sílaba tônica das palavras que estão em homografia com outras em que são abertos êsse
e e êsse o: acêrto (s.m.) e acerto (v.); aquêle, aquêles (adj. ou pron. dem.) e aquele,
aqueles (v.); côr (s.f.) e cor (s.m.); côrte, côrtes (s.f.) e corte, cortes (v.); dêle,
dêles [...]; devêras (v.) e deveras (adv.); êsse, êsses, êste, êstes [...]; fêz (s.m. e
v.) e fez (s.f.); fôr (v.) e for (s.m.); fôra (v.) e fora [...]; fôsse [...]; nêle,
nêles [...]; pôde (perf. ind.) e pode (pres. ind.); sôbre (prep.) e sobre (v.), etc."
Its OBSERVAÇÃO 2.ª adds enfêrmo, enfêrma, enfêrmas, colhêr and colhêres. The law keeps
only pôde, so each other word loses the circumflex on every route from a norm before
1971 to br_1971 or ao1990-br.
"""
import pytest

from desacordo_ortografico import convert

SOURCES = ("br_1943", "reforma_1911", "etymological")
TARGETS = ("br_1971", "ao1990-br")

DROPPED = [
    ("sôbre", "sobre"),
    ("aquêle", "aquele"),
    ("aquêles", "aqueles"),
    ("côr", "cor"),
    ("dêle", "dele"),
    ("dêles", "deles"),
    ("êsse", "esse"),
    ("êsses", "esses"),
    ("êste", "este"),
    ("êstes", "estes"),
    ("fêz", "fez"),
    ("fôr", "for"),
    ("fôra", "fora"),
    ("fôsse", "fosse"),
    ("nêle", "nele"),
    ("nêles", "neles"),
    ("enfêrmo", "enfermo"),
    ("enfêrma", "enferma"),
    ("enfêrmas", "enfermas"),
]

# The bare form of each of these words is the more frequent reading of the pair (o corte,
# deveras, a colher), and the 1971 table is also the backward map: a row for one of them
# would put the circumflex on that reading at br_1943.
NOT_LISTED = [
    ("acêrto", "acerto"),
    ("côrte", "corte"),
    ("côrtes", "cortes"),
    ("devêras", "deveras"),
    ("colhêr", "colher"),
    ("colhêres", "colheres"),
]


@pytest.mark.parametrize("dst", TARGETS)
@pytest.mark.parametrize("src", SOURCES)
@pytest.mark.parametrize("word,bare", DROPPED)
def test_circumflex_dropped(word, bare, src, dst):
    assert convert(word, src, dst) == bare


@pytest.mark.xfail(strict=True, reason="desacordo#70")
@pytest.mark.parametrize("dst", TARGETS)
@pytest.mark.parametrize("src", SOURCES)
@pytest.mark.parametrize("word,bare", NOT_LISTED)
def test_circumflex_dropped_not_listed(word, bare, src, dst):
    assert convert(word, src, dst) == bare


@pytest.mark.parametrize("dst", TARGETS)
@pytest.mark.parametrize("src", SOURCES)
def test_pode_keeps_the_circumflex(src, dst):
    assert convert("pôde", src, dst) == "pôde"


@pytest.mark.parametrize("dst", TARGETS)
def test_sentence(dst):
    assert convert("Sôbre êles, fêz o que pôde.", "br_1943", dst) == "Sobre eles, fez o que pôde."


# The law abolishes the accent on the word, so a word inside a hyphenated form loses it too.
HYPHENATED = [
    ("fêz-se", "fez-se"),
    ("fôr-lhe", "for-lhe"),
    ("sôbre-humano", "sobre-humano"),
    ("côr-de-rosa", "cor-de-rosa"),
]


@pytest.mark.parametrize("dst", TARGETS)
@pytest.mark.parametrize("src", SOURCES)
@pytest.mark.parametrize("word,bare", HYPHENATED)
def test_circumflex_dropped_in_hyphenated_form(word, bare, src, dst):
    assert convert(word, src, dst) == bare
