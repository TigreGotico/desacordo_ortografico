"""AO1990 -> older norms: the accents AO1990 Base IX 9.o dropped.

The bare form is also a proclitic in daily use (para, pela, pelo), so it stays as
written; only context separates the two, which is bifonia's job. pera and polo(s)
get their accent back, because their proclitic reading is archaic: pera,
"preposição arcaica" (Acordo de 1945, Base XXII, which also says the plural peras
takes no accent), and polo(s), "combinação antiga e popular de por e lo(s)"
(AO1990 Base IX 9.o).
"""
import pytest

from desacordo_ortografico import convert

PAIRS = [("ao1990-pt", "pt_1973"), ("ao1990-br", "br_1971")]


@pytest.mark.parametrize("src,dst", PAIRS)
@pytest.mark.parametrize("text", [
    "Passou pelo caminho.",
    "Passou pelos campos.",
    "Vou pela rua.",
    "Vou pelas ruas.",
    "Vou para casa.",
    "As peras.",
])
def test_proclitic_stays_as_written(text, src, dst):
    assert convert(text, src, dst) == text


@pytest.mark.parametrize("src,dst", PAIRS)
@pytest.mark.parametrize("text,old", [
    ("Comi uma pera.", "Comi uma pêra."),
    ("O polo norte.", "O pólo norte."),
    ("Os polos.", "Os pólos."),
])
def test_archaic_competitor_restored(text, old, src, dst):
    assert convert(text, src, dst) == old


@pytest.mark.parametrize("src,dst", [(d, s) for s, d in PAIRS])
def test_forward_still_drops_the_accent(src, dst):
    assert convert("O pêlo, a pêra e o pólo.", src, dst) == "O pelo, a pera e o polo."
