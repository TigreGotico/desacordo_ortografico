"""ao1990-br writes the concept* words with the p, as the ABL VOLP lists them.

The VOLP search "concept" lists conceptacular adj.2g., conceptáculo s.m.,
conceptibilidade s.f., conceptismo s.m., conceptista adj. s.2g., conceptístico adj.,
conceptível adj.2g., concepto adj., conceptual adj.2g., conceptualismo s.m.,
conceptualista adj. s.2g., conceptualístico adj., conceptualização s.f., conceptualizado
adj., conceptualizador (ô) adj. s.m., conceptualizante adj.2g., conceptualizar v.,
conceptualizável adj.2g. and conceptuoso (ô) adj. The search "concet" gives no row. So
the pt-PT form without the p takes the p at ao1990-br.
"""
import pytest

from desacordo_ortografico import convert

VOLP_FORMS = [
    "conceptacular", "conceptáculo", "conceptibilidade", "conceptismo", "conceptista",
    "conceptístico", "conceptível", "concepto", "conceptual", "conceptualismo",
    "conceptualista", "conceptualístico", "conceptualização", "conceptualizado",
    "conceptualizador", "conceptualizante", "conceptualizar", "conceptualizável",
    "conceptuoso",
]


@pytest.mark.parametrize("full", VOLP_FORMS)
def test_the_bare_form_takes_the_volp_p(full):
    bare = full.replace("concept", "concet", 1)
    assert convert(bare, "ao1990-pt", "ao1990-br") == full


@pytest.mark.parametrize("full", VOLP_FORMS)
@pytest.mark.parametrize("source", ("ao1990-pt", "pt_1973", "br_1971"))
def test_the_volp_form_stays(full, source):
    assert convert(full, source, "ao1990-br") == full


def test_sentence():
    text = "Um quadro concetual ajuda a concetualizar os modelos concetuais."
    assert convert(text, "ao1990-pt", "ao1990-br") == (
        "Um quadro conceptual ajuda a conceptualizar os modelos conceptuais.")
