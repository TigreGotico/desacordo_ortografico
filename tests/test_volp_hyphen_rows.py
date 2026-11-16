"""The ABL VOLP decides a joined prefix word at ao1990-br, through the rows of
data/volp_ao1990_br.json.

The VOLP writes contra-erva ("contra-erva s.f.; pl. contra-ervas") and macro-jê ("macro-jê
adj. s.2g.; pl. macro-jês") with the hyphen, so the Base XVI join gives way to the VOLP
form at ao1990-br. The VOP writes contraerva (lemma 80805), so ao1990-pt joins.
"""
import pytest

from desacordo_ortografico import convert
from desacordo_ortografico.lexicon import Lexicon


@pytest.mark.parametrize("word", ["contra-erva", "contra-ervas", "macro-jê", "macro-jês"])
def test_the_volp_form_keeps_the_hyphen_at_ao1990_br(word):
    assert convert(word, "br_1971", "ao1990-br") == word


def test_the_volp_form_keeps_the_hyphen_in_a_sentence():
    text = "A contra-erva cresce onde se falam línguas macro-jê."
    assert convert(text, "br_1971", "ao1990-br") == text


@pytest.mark.parametrize("old, new", [("contra-erva", "contraerva"), ("contra-ervas", "contraervas")])
def test_the_vop_form_joins_at_ao1990_pt(old, new):
    assert convert(old, "pt_1973", "ao1990-pt") == new


def test_a_hyphenated_plural_in_a_quote_is_listed_whole():
    listed = Lexicon().ao_br_volp_listed
    assert "contra-ervas" in listed and "macro-jês" in listed
    assert "contra" not in listed and "macro" not in listed
