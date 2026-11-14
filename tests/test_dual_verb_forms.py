"""A verb form with one pt-PT spelling does not gain the consonant of a dual adjective.

The VOP (Vocabulário Ortográfico do Português, Portal da Língua Portuguesa) gives the
adjectives infeto and interceto as pt-PT pairs (Base IV 1º c), and the verbs infetar and
intercetar as single in Portugal. The pre-AO1990 pt-PT form of the verb and of the
adjective is infecto (Priberam, infeto: "Grafia anterior ao Acordo Ortográfico de 1990:
infecto"), so the routes out of ao1990-pt keep the consonant.
"""
import pytest

from desacordo_ortografico import convert

SOURCES = ("pt_1973", "etymological", "br_1971", "ao1990-br")


@pytest.mark.parametrize("src", SOURCES)
def test_infetar_first_person_stays_as_written(src):
    """VOP lemma 37066: "infetar - verbo ... infeto infetas infeta ... variante AO de :
    infectar ( Brasil)"."""
    assert convert("Eu infeto a ferida.", src, "ao1990-pt") == "Eu infeto a ferida."


@pytest.mark.parametrize("src", SOURCES)
def test_intercetar_first_person_stays_as_written(src):
    """VOP lemma 191891: "intercetar - verbo ... Portugal ... interceto intercetas
    interceta ... variante AO : interceptar ( Brasil)"."""
    assert convert("Eu interceto a bola.", src, "ao1990-pt") == "Eu interceto a bola."


def test_pre_ao1990_verb_form_drops_the_c():
    """VOP lemma 37066: infetar is the pt-PT form, "variante AO de : infectar ( Brasil)"."""
    assert convert("Eu infecto a ferida.", "pt_1973", "ao1990-pt") == "Eu infeto a ferida."


def test_singular_adjective_takes_the_bare_form():
    """VOP lemma 12090: "infeto - adjetivo ... variante AO : infecto". Both forms are pt-PT,
    so the bare form of the frequent verb reading is a valid adjective too."""
    assert convert("O material infecto.", "pt_1973", "ao1990-pt") == "O material infeto."


@pytest.mark.parametrize("src, text, out", [
    ("pt_1973", "Os tecidos infectos.", "Os tecidos infectos."),
    ("ao1990-br", "Os tecidos infetos.", "Os tecidos infectos."),
    ("ao1990-br", "Os sinais intercetos.", "Os sinais interceptos."),
])
def test_adjective_plural_still_takes_the_consonant(src, text, out):
    """VOP lemma 12090 "Plural infetos infetas ... variante AO : infecto" and lemma 191893
    "interceto - adjetivo ... Plural intercetos intercetas ... variante AO de : intercepto".
    The plurals are no verb forms, so the dual step writes the form with the consonant."""
    assert convert(text, src, "ao1990-pt") == out


@pytest.mark.parametrize("dst", ("pt_1973", "etymological"))
@pytest.mark.parametrize("text, out", [
    ("Eu infeto a ferida.", "Eu infecto a ferida."),
    ("O material infeto.", "O material infecto."),
    ("Os tecidos infetos.", "Os tecidos infectos."),
])
def test_route_out_of_ao1990_pt_restores_the_c(dst, text, out):
    """VOP lemma 15917 "infectar - verbo ... variante AO : infetar" and Priberam, infeto:
    "Grafia anterior ao Acordo Ortográfico de 1990: infecto"."""
    assert convert(text, "ao1990-pt", dst) == out
