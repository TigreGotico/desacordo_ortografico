"""Brazilian spelling keeps the p of óptica, the science of vision.

ABL, Pequeno Vocabulário Ortográfico da Língua Portuguesa (1943), p. 964: "óptica, s. f.:
ótica." It lists ótica beside óptica and has no headword ótica of its own, so both forms
are valid in 1943, and the form with the consonant is written. VOLP: óptica s.f. "ciência
da visão"; cf. ótica ("ciência da audição"): two words, so ao1990-br keeps óptica.
pt-PT drops the p (VOP: ótica, with óptica tagged Brasil).
"""
import pytest

from desacordo_ortografico import convert

TEXT = "A óptica do oftalmologista."


@pytest.mark.parametrize("target", ("br_1943", "br_1971", "ao1990-br"))
def test_etymological_optica_keeps_the_p_in_brazil(target):
    assert convert(TEXT, "etymological", target) == TEXT


@pytest.mark.parametrize("source", ("etymological", "pt_1973"))
def test_optica_drops_the_p_in_pt_pt(source):
    assert convert(TEXT, source, "ao1990-pt") == "A ótica do oftalmologista."


def test_br_group_keeps_optica():
    features = {"1911-word-map", "base-iv", "initial-sc", "ptbr-divergence", "hyphen-lexical"}
    assert convert(TEXT, "etymological", "ao1990-br", features=features) == TEXT
