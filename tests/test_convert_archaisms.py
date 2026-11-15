"""The rows of the tugalex archaisms list in the forward pass of the 1911 edge.

Each expected value comes from a row of the tugalex ``archaisms.csv`` list (archaic,
modern, modern_pt_BR) and from the Formulário Ortográfico of 1911 (Portal da Língua
Portuguesa, ILTEC), not from the converter.

Base XV: "No interior dos vocábulos é a nasalidade da vogal expressa por m antes de b, p,
m, e por n em qualquer outra situação". The rows emquanto -> enquanto, bemdito -> bendito,
comsigo -> consigo and emfim -> enfim follow it, and the VOP (Portal da Língua Portuguesa)
gives enquanto, bendito, consigo and enfim and none of the old forms.

Base IX keeps a consonant "quando influam no valor da vogal que as precede; ex.:
contracção, reacção, direcção, excepção". So the 1911 form of the row architecto ->
arquiteto is arquitecto, the pre-AO1990 form that the AO1990 pt-PT word map of tugalex
gives for arquiteto. The row excepcionaes -> excecionais writes excepcionais in its pt-BR
column.

Base XI keeps the initial sc of "scena, sciência, scetro, scéptico, scisma, scisão,
sciático, scintilar", so the row scintillar -> cintilar gives no 1911 form. Base VIII drops
a silent consonant ("autor, restrito, produto") and Base IX keeps one that opens the vowel,
so the row affectando -> afetando (AO1990 afetar, before AO1990 afectar) gives no 1911
form either.

The row colleccionador -> colecionador has no pt-BR value, so pt-BR writes colecionador
too. Its 1911 form coleccionador keeps a c that no Brazilian table drops, so the row stays
out of the shared 1911 map.
"""
import pytest

from desacordo_ortografico import FEATURES, convert
from desacordo_ortografico.lexicon import get_lexicon

ALL_TARGETS = ["reforma_1911", "pt_1945", "pt_1973", "ao1990-pt", "br_1943", "br_1971", "ao1990-br"]


@pytest.mark.parametrize("target", ALL_TARGETS)
def test_base_xv_rows_convert_into_every_later_norm(target):
    assert convert("Emquanto isso, bemdito seja.", "etymological", target) == "Enquanto isso, bendito seja."


@pytest.mark.parametrize("target", ["reforma_1911", "ao1990-pt", "ao1990-br"])
@pytest.mark.parametrize("text,expected", [
    ("Tyranno e cego, e cego até comsigo?", "Tirano e cego, e cego até consigo?"),
    ("penoso emfim se alcança?", "penoso enfim se alcança?"),
])
def test_pt_dii_rows(text, expected, target):
    assert convert(text, "etymological", target) == expected


@pytest.mark.parametrize("old,target,expected", [
    ("architecto", "reforma_1911", "arquitecto"),
    ("architecto", "pt_1973", "arquitecto"),
    ("architecto", "ao1990-pt", "arquiteto"),
    ("architecto", "ao1990-br", "arquiteto"),
    ("excepcionaes", "reforma_1911", "excepcionais"),
    ("excepcionaes", "ao1990-pt", "excecionais"),
    ("excepcionaes", "ao1990-br", "excepcionais"),
])
def test_row_with_an_ao1990_change_gives_the_pre_ao1990_form_in_1911(old, target, expected):
    assert convert(old, "etymological", target) == expected


@pytest.mark.parametrize("old,expected", [("scintillar", "scintilar"), ("affectando", "afectando")])
def test_row_without_a_known_1911_form_stays_out(old, expected):
    assert convert(old, "etymological", "reforma_1911") == expected


@pytest.mark.parametrize("target", ["ao1990-pt", "ao1990-br"])
def test_row_the_brazilian_edges_cannot_reach_stays_out(target):
    assert convert("colleccionador", "etymological", target) == "colecionador"


@pytest.mark.parametrize("text,expected", [
    ("Enquanto isso, bendito seja.", "Enquanto isso, bendito seja."),
    ("consigo", "consigo"),
    ("arquiteto", "arquitecto"),
])
def test_backward_pass_reads_no_archaism(text, expected):
    assert convert(text, "ao1990-pt", "etymological") == expected


def test_accent_restore_after_the_1911_pass():
    assert convert("fosforo e emquanto", "etymological", "reforma_1911") == "fósforo e enquanto"


def test_word_map_feature_gates_the_archaisms():
    features = FEATURES - {"1911-word-map"}
    assert convert("emquanto", "etymological", "reforma_1911", features=features) == "emquanto"


@pytest.mark.parametrize("archaic,modern,row_class", [
    ("comsigo", "consigo", "1911"),
    ("architecto", "arquiteto", "ao1990-map"),
    ("affectando", "afetando", "ao1990-cp"),
    ("auctor", "autor", "ao1990-cp"),
    ("pello", "pelo", "ao1990-differential"),
    ("scintillar", "cintilar", "sc"),
])
def test_archaism_row_class(archaic, modern, row_class):
    from desacordo_ortografico.convert import archaism_row_class

    assert archaism_row_class(archaic, modern, get_lexicon()) == row_class
