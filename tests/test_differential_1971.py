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
    ("fôsse", "fosse"),
    ("nêle", "nele"),
    ("nêles", "neles"),
    ("enfêrmo", "enfermo"),
    ("enfêrma", "enferma"),
    ("enfêrmas", "enfermas"),
]

# The bare form of each of these words is the more frequent reading of the pair (o corte,
# deveras, a colher; fora is an adverb 45 times and a preposition twice against 7 uses as the
# verb, in UD Bosque). They are forward-only rows: the accent goes toward br_1971 and
# ao1990-br, and the bare form stays bare going back.
FORWARD_ONLY = [
    ("acêrto", "acerto"),
    ("côrte", "corte"),
    ("côrtes", "cortes"),
    ("devêras", "deveras"),
    ("colhêr", "colher"),
    ("colhêres", "colheres"),
    ("fôra", "fora"),
]


@pytest.mark.parametrize("dst", TARGETS)
@pytest.mark.parametrize("src", SOURCES)
@pytest.mark.parametrize("word,bare", DROPPED + FORWARD_ONLY)
def test_circumflex_dropped(word, bare, src, dst):
    assert convert(word, src, dst) == bare


@pytest.mark.parametrize("dst", ("br_1943", "reforma_1911", "etymological"))
@pytest.mark.parametrize("src", TARGETS)
@pytest.mark.parametrize("word,bare", FORWARD_ONLY)
def test_a_forward_only_word_stays_bare_going_back(word, bare, src, dst):
    assert convert(bare, src, dst) == bare


@pytest.mark.parametrize("old, new", [
    ("Êle está lá fôra.", "Ele está lá fora."),
    ("O acêrto da côrte devêras agradou.", "O acerto da corte deveras agradou."),
    ("Vou colhêr as flores e dois colhêres.", "Vou colher as flores e dois colheres."),
])
def test_forward_only_words_in_a_sentence(old, new):
    assert convert(old, "br_1943", "br_1971") == new


def test_the_bare_sentence_keeps_its_readings_going_back():
    assert convert("Ele está lá fora.", "ao1990-br", "br_1943") == "Êle está lá fora."
    assert convert("Foi ao corte e deveras gostou.", "br_1971", "br_1943") == "Foi ao corte e deveras gostou."


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
