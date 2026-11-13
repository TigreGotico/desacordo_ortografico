"""The silent c/p rule must not turn a valid word into another word.

AO1990 Base IV 1º keeps a c or p that is pronounced (a, c) and drops one that is mute
(b). Each word in KEPT keeps its consonant in the tugalex regional dictionary (lbx IPA:
aptitude ɐp|ti|tˈud, copta kˈɔp|tɐ, inapto i|nˈap|tu, raptar ʀɐp|tˈaɾ,
críptico kɾˈip|ti|ku, políptico pu|lˈip|ti|ku, lactente lɐk|tˈẽt, secção sɛk|sˈɐ̃w),
and the tugalex pt-PT AO1990 map has no row for it. So AO1990 leaves it as written.
The words in MUTE sound the same with and without the consonant in the same
dictionary (contracto and contrato kõ|tɾˈa|tu, contractura and contratura
kõ|tɾɐ|tˈu|ɾɐ), so the consonant goes.
"""
import pytest
from tugalex import TugaLexicon

from desacordo_ortografico import convert

KEPT = ["aptitude", "copta", "inapto", "raptar", "críptico", "políptico", "lactente",
        "secção"]
MUTE = [("contracto", "contrato"), ("contractura", "contratura")]


@pytest.fixture(scope="module")
def ao_pt_map():
    return TugaLexicon().ao_pt


def test_sentence_keeps_all_three_words():
    text = "A aptitude do copta inapto."
    assert convert(text, "pre-ao1990-pt", "ao1990-pt") == text


@pytest.mark.parametrize("word", KEPT)
def test_valid_word_is_kept(word, ao_pt_map):
    assert word not in ao_pt_map
    assert convert(word, "pre-ao1990-pt", "ao1990-pt") == word


@pytest.mark.parametrize("old,new", [
    # AO1990 Base IV 1º c): the mute c/p of afectivo, activo and adoptar goes,
    # inflections included
    ("afectiva", "afetiva"),
    ("activos", "ativos"),
    ("adoptada", "adotada"),
])
def test_inflection_outside_the_map_still_drops(old, new):
    assert convert(old, "pre-ao1990-pt", "ao1990-pt") == new


@pytest.mark.parametrize("old,new", MUTE)
def test_attested_word_with_a_mute_consonant_drops_it(old, new):
    assert convert(old, "pre-ao1990-pt", "ao1990-pt") == new
