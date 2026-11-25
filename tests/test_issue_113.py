"""ao1990-br to ao1990-pt drops the c or p that the European norm does not pronounce."""

import pytest

from desacordo_ortografico import convert

# AO1990 Base IV 1.º b) drops a c or p that is not pronounced in the European norm.
_DROPPED = {
    "óptimo": "ótimo",
    "colectivo": "coletivo",
    "afecta": "afeta",
    "insecto": "inseto",
    "lectivo": "letivo",
}

# AO1990 Base IV 1.º a) keeps a c or p that is pronounced in every norm.
_KEPT = ["compacto", "adepto", "pacto", "apto", "rapto"]


@pytest.mark.xfail(
    strict=True,
    reason="https://github.com/TigreGotico/desacordo_ortografico/issues/113: "
           "ao1990-br to ao1990-pt keeps the mute c or p of óptimo")
def test_br_to_pt_drops_the_mute_consonant():
    for word, expected in _DROPPED.items():
        assert convert(word, "ao1990-br", "ao1990-pt") == expected, word
    # A fix that drops every c or p before a consonant breaks these.
    for word in _KEPT:
        assert convert(word, "ao1990-br", "ao1990-pt") == word, word
