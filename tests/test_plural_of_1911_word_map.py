"""The plural of a word that the 1911 word map holds follows the row.

Each expected value is the singular's own row plus the regular plural of Portuguese: a word
in a vowel or an oral diphthong takes -s. Cunha & Cintra, Nova Gramática do Português
Contemporâneo, 7.ª ed., pp. 194-196, "Substantivos terminados em vogal ou ditongo": "O plural
dos substantivos terminados em vogal ou ditongo forma-se acrescentando-se -s ao singular",
with peru -> perus, pau -> paus, chapéu -> chapéus, camafeu -> camafeus, herói -> heróis and
javali -> javalis. The rows are chimica -> química, machina -> máquina, echo -> eco,
symphonia -> sinfonia and analyse -> análise, so chimicas -> químicas, machinas -> máquinas,
echos -> ecos, symphonias -> sinfonias and analyses -> análises. A row in -u or -i takes the
same -s: museo -> museu, so museos -> museus; chapéo -> chapéu, so chapeos -> chapéus.
"""
import pytest

from desacordo_ortografico import convert


def to_1911(word):
    return convert(word, "etymological", "reforma_1911")


@pytest.mark.parametrize("singular,plural", [
    ("chimica", "químicas"),
    ("machina", "máquinas"),
    ("echo", "ecos"),
    ("symphonia", "sinfonias"),
    ("analyse", "análises"),
])
def test_the_plural_of_a_row_is_its_value_plus_s(singular, plural):
    assert to_1911(singular + "s") == plural
    assert to_1911(singular + "s") == to_1911(singular) + "s"


@pytest.mark.parametrize("word,expected", [
    ("Chimicas", "Químicas"),
    ("CHIMICAS", "QUÍMICAS"),
])
def test_the_plural_keeps_the_case_of_the_input(word, expected):
    assert to_1911(word) == expected


@pytest.mark.parametrize("word", ["casas", "amigas"])
def test_a_word_with_no_row_stays(word):
    assert to_1911(word) == word


def test_wagons_takes_the_plural_of_vagao():
    # wagon -> vagão; the plural of vagão is vagões, not vagão + s
    assert to_1911("wagons") == "vagões"


@pytest.mark.parametrize("singular, plural", [
    ("museo", "museus"),
    ("pao", "paus"),
    ("papae", "papais"),
    ("seo", "seus"),
    ("chapeo", "chapéus"),
    ("veo", "véus"),
    ("mausoléo", "mausoléus"),
])
def test_a_value_in_u_or_i_takes_s(singular, plural):
    assert to_1911(singular + "s") == plural
    assert to_1911(singular + "s") == to_1911(singular) + "s"


@pytest.mark.parametrize("word", ["meos", "europeos", "andas"])
def test_a_word_with_no_singular_row_stays_in_u_or_i_too(word):
    assert to_1911(word) == word


def test_the_plural_reaches_the_later_edges():
    assert convert("chimicas", "etymological", "ao1990-pt") == "químicas"
    assert convert("machinas", "etymological", "ao1990-br") == "máquinas"
