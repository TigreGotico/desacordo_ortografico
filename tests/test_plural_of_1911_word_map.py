"""The plural of a word that the 1911 word map holds follows the row.

Each expected value is the singular's own row plus the regular plural of Portuguese: a word
in -a, -e or -o takes -s. The rows are chimica -> química, machina -> máquina, echo -> eco,
symphonia -> sinfonia and analyse -> análise, so chimicas -> químicas, machinas -> máquinas,
echos -> ecos, symphonias -> sinfonias and analyses -> análises. A row whose value does not
end in -a, -e or -o (museo -> museu, pao -> pau) takes no derived plural: its plural is not
the value plus -s.
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


# A value in -u or -i takes -s as well: museo -> museu gives museus, pao -> pau gives
# paus, papae -> papai gives papais. lookup_with_plural derives no plural for these.
@pytest.mark.xfail(strict=True, reason="no derived plural for a value in -u or -i (#81)")
@pytest.mark.parametrize("word, expected", [("museos", "museus"), ("paos", "paus"), ("papaes", "papais")])
def test_a_value_in_u_or_i_takes_s(word, expected):
    assert to_1911(word) == expected


def test_the_plural_reaches_the_later_edges():
    assert convert("chimicas", "etymological", "ao1990-pt") == "químicas"
    assert convert("machinas", "etymological", "ao1990-br") == "máquinas"
