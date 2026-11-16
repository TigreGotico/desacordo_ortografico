"""A loanword that the vocabulary of the target variety lists with its hyphen keeps it.

The rows of data/hyphen_loanwords.json come from a prefix search of each vocabulary for
every prefix of the AO1990 Base XVI join and a hyphen. The ABL VOLP (pt-BR) marks four of
its entries "Estrangeira" ("Este verbete faz parte do Vocabulário de Estrangeirismos"):
co-worker, co-working, mini-show and mini-system. The VOP of the Portal da Língua
Portuguesa (pt-PT) marks three of its entries "estrangeirismo": anti-apartheid
(neerlandês), anti-dumping and anti-establishment (inglês). Neither vocabulary lists
co-op, multi-user or auto-update, so those still join.
"""
import pytest

from desacordo_ortografico import convert, rules


@pytest.mark.parametrize("word", ["co-worker", "co-working", "mini-show", "mini-system"])
def test_a_volp_loanword_keeps_the_hyphen_toward_pt_br(word):
    assert convert(word, "br_1971", "ao1990-br") == word


@pytest.mark.parametrize("word", ["anti-apartheid", "anti-dumping", "anti-establishment"])
def test_a_vop_loanword_keeps_the_hyphen_toward_pt_pt(word):
    assert convert(word, "pt_1973", "ao1990-pt") == word


def test_the_listed_loanword_keeps_its_hyphen_in_a_sentence():
    assert convert("Uma lei anti-apartheid.", "pt_1973", "ao1990-pt") == "Uma lei anti-apartheid."


@pytest.mark.parametrize("source, target", [("pt_1973", "br_1971"), ("br_1971", "ao1990-br")])
@pytest.mark.parametrize("text", ["o mini-systems", "os mini-shows"])
def test_the_english_plural_of_a_volp_loanword_keeps_the_hyphen(text, source, target):
    assert convert(text, source, target) == text


def test_the_plural_rule_of_the_other_tables_stays_portuguese():
    # only the loanword rows give an English plural; rules.lookup_with_plural keeps the
    # Portuguese plurals (aspetos from aspeto) and finds no -s plural of a final consonant
    table = {"mini-system": "mini-system", "aspeto": "aspeto"}
    assert rules.lookup_with_plural("aspetos", table) == "aspetos"
    assert rules.lookup_with_plural("mini-systems", table) is None
