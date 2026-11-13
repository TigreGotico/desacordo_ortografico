"""The trema rule keeps ü in derivatives of foreign names.

AO1990 Base XIV 1º suppresses the trema in Portuguese words. Its Obs. keeps the trema in
words derived from foreign proper names, after Base I 3º: "hübneriano, de Hübner,
mülleriano, de Müller". The expected values below are the words of those clauses.
"""
import pytest

from desacordo_ortografico import convert

TARGETS = ("pt_1945", "pt_1973", "ao1990-pt", "br_1971", "ao1990-br")

# AO1990 Base XIV 1º Obs. and Base I 3º, verbatim
FOREIGN = ["hübneriano", "Hübner", "mülleriano", "Müller"]


@pytest.mark.parametrize("word", FOREIGN)
@pytest.mark.parametrize("target", TARGETS)
def test_foreign_derivative_keeps_trema(word, target):
    assert convert(f"o {word}", "etymological", target) == f"o {word}"


@pytest.mark.parametrize("word", FOREIGN)
def test_foreign_derivative_keeps_trema_br_to_ao(word):
    assert convert(f"o {word}", "br_1971", "ao1990-br") == f"o {word}"


# AO1990 Base XIV 1º: the AO1990 forms are verbatim; the input is the same word with the
# trema that the 1943 Formulário wrote on a pronounced u after g or q.
PORTUGUESE = ["aguentar", "arguir", "bilíngue", "lingueta", "linguista", "linguístico",
              "cinquenta", "equestre", "frequentar", "tranquilo", "ubiquidade"]


@pytest.mark.parametrize("word", PORTUGUESE)
def test_portuguese_word_drops_trema_after_g_or_q(word):
    old = word.replace("gu", "gü").replace("qu", "qü")
    assert convert(old, "br_1971", "ao1990-br") == word


# AO1990 Base XIV 1º: "saudade, e não saüdade"; "saudar, e não saüdar"
@pytest.mark.parametrize("old, new", [("saüdade", "saudade"), ("saüdar", "saudar")])
def test_hiatus_trema_drops(old, new):
    assert convert(old, "reforma_1911", "pt_1945") == new
