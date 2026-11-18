"""Pre-1911 Esther is the given name Ester, with no accent.

ABL, Pequeno Vocabulário Ortográfico da Língua Portuguesa (1943): "éster, s. m./Cf. Ester,
antr., e hester." The name Ester and the chemical éster are two words. The Portuguese
register of given names (IRN, Vocabulários admitidos e não admitidos como nomes próprios)
admits Ester and not Esther. A capital marks the name, so the 1911 accent guess does not
give it the accent of éster. A lowercase esther is the common word.
"""
import pytest

from desacordo_ortografico import convert

TARGETS = ("reforma_1911", "pt_1945", "pt_1973", "br_1943", "br_1971", "ao1990-pt", "ao1990-br")


@pytest.mark.parametrize("target", TARGETS)
def test_esther_gives_the_name_ester(target):
    assert convert("Esther", "etymological", target) == "Ester"
    assert convert("O livro de Esther.", "etymological", target) == "O livro de Ester."


@pytest.mark.parametrize("target", TARGETS)
def test_a_lowercase_esther_gives_the_chemical(target):
    assert convert("esther", "etymological", target) == "éster"
