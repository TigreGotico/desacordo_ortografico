"""A foreign word that the vocabularies list keeps its spelling under the 1911 rules.

The 1911 Formulário, Base I, covers "todas as palavras portuguesas, ou aportuguesadas". The
VOP (Portal da Língua Portuguesa) marks "apartheid - nome masculino" (lemma 89882, "estrangeirismo;
língua de origem: neerlandês"), "hall - nome masculino" (13211, inglês) and "byte - nome
masculino" (107007, inglês, "variante : baite ( Brasil)"). The VOLP marks "apartheid s.m.
ing.Estrangeira", "hall s.m. ing.Estrangeira", "byte s.m. ing.Estrangeira" and "affaire s.m.
fr.Estrangeira", each with "Este verbete faz parte do Vocabulário de Estrangeirismos".

A spelling mark fails here: nothing in apartheid, hall or byte marks a foreign word that a
Portuguese pre-1911 word lacks. The attested-word check fails on byte: bite is a Portuguese word
in the VOLP ("bite s.m.") and a form of bitar in the VOP (lemma 147496).
"""
import pytest

from desacordo_ortografico import convert

TARGETS = ("reforma_1911", "pt_1973", "br_1971", "ao1990-pt", "ao1990-br")


@pytest.mark.parametrize("target", TARGETS)
@pytest.mark.parametrize("text", [
    "O apartheid acabou em 1994.",
    "Os apartheids do mundo.",
    "O affaire de Estado.",
    "Esperou no hall do hotel.",
    "Um byte tem oito bits.",
    "Dois bytes bastam.",
    "HALL E BYTE",
    "Hall",
])
def test_a_listed_foreign_word_stays_as_written(text, target):
    assert convert(text, "etymological", target) == text


@pytest.mark.parametrize("features, text", [
    ({"1911-digraphs"}, "O apartheid, o hall e o byte."),
    ({"1911-geminates"}, "O apartheid, o affaire e o hall."),
    ({"1911-digraphs", "1911-geminates"}, "O apartheid, o affaire, o hall e o byte."),
])
def test_a_listed_foreign_word_stays_under_each_feature(features, text):
    assert convert(text, "etymological", "ao1990-pt", features=features) == text


@pytest.mark.parametrize("old, new, features", [
    ("a phlebite", "a flebite", {"1911-digraphs"}),
    ("o sabbatico", "o sabatico", {"1911-geminates"}),
    ("a phlebite do apartheid", "a flebite do apartheid", {"1911-digraphs"}),
    ("o hall sabbatico", "o hall sabatico", {"1911-geminates"}),
])
def test_a_portuguese_word_still_follows_the_rules(old, new, features):
    assert convert(old, "etymological", "ao1990-pt", features=features) == new


def test_a_portuguese_sentence_next_to_a_listed_word_converts():
    assert convert("O apartheid e a pharmacia do hall.", "etymological", "ao1990-pt") == \
        "O apartheid e a farmácia do hall."
