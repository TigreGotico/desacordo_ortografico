"""The bare form of a dual stays as written under the tugaphone feature groups.

AO1990 Base IV 1.º c) leaves the choice between the two forms to the writer ("facto e fato,
sector e setor ... caracteres e carateres"), and the feature groups of the tugaphone spelling
step leave out `volp` and `silent-cp`, the two features that choose one form. So modern text
that writes the bare form keeps it, and a speaker reads the consonant that the writer
wrote. The silver selection of test_modern_text_unchanged.py holds only rows whose pre-1990
cell equals the AO1990 cell, and the AO1990 cell of a dual writes the c/p form, so those
rows fall out. This file pins each bare form.

pt-BR, each form its own entry of the VOLP (ABL): "fato s.m." and "facto s.m."; "ótimo adj.
s.m. interj." and "óptimo adj. s.m. interj."; "contato s.m." and "contacto s.m."; "setor (ô)
s.m." and "sector (ô) s.m."; "eletrônico adj." and "electrônico adj.".

pt-PT, the VOP (Portal da Língua Portuguesa): lemma 117204 "setor - nome masculino ...
variante AO : sector" and lemma 47603 "sector ... variante AO de : setor"; lemma 87085
"caráter - nome masculino ... variante AO : carácter ( Portugal)" and lemma 48215 "carácter";
lemma 35619 "acupuntura - nome feminino ... variante AO : acupunctura" and lemma 106786
"acupunctura ... variante AO de : acupuntura".

With every feature, the volp step writes the c/p form of a dual by a preference for the
consonant. A form that the vocabulary records as valid in the source should stay as written
(TigreGotico/desacordo_ortografico#116), and the xfail tests below expect that.
"""
import pytest

from desacordo_ortografico import convert

PT_GROUP = frozenset({"1911-word-map", "trema", "ao-map-consonant", "base-iv",
                      "initial-sc", "ao-map-diacritic"})
BR_GROUP = frozenset({"1911-word-map", "base-iv", "initial-sc", "ptbr-divergence",
                      "hyphen-lexical"})

# bare form, then the form with the consonant
BR_DUALS = [
    ("O fato é ótimo.", "O facto é óptimo."),
    ("O contato com o setor eletrônico.", "O contacto com o sector electrônico."),
    ("Os fatos, os setores e os contatos eletrônicos.", "Os factos, os sectores e os contactos electrônicos."),
]
PT_DUALS = [
    ("O setor tem o caráter da acupuntura.", "O sector tem o carácter da acupunctura."),
    ("Os setores e os caracteres.", "Os sectores e os caracteres."),
]


@pytest.mark.parametrize("source", ["etymological", "br_1971"])
@pytest.mark.parametrize("bare, _full", BR_DUALS)
def test_br_group_keeps_the_bare_dual(bare, _full, source):
    assert convert(bare, source, "ao1990-br", features=BR_GROUP) == bare


@pytest.mark.parametrize("source", ["etymological", "pt_1973"])
@pytest.mark.parametrize("bare, _full", PT_DUALS)
def test_pt_group_keeps_the_bare_dual(bare, _full, source):
    assert convert(bare, source, "ao1990-pt", features=PT_GROUP) == bare


@pytest.mark.xfail(strict=True, reason="desacordo#116: the volp step writes facto where fato is valid")
@pytest.mark.parametrize("bare, _full", BR_DUALS)
def test_a_valid_bare_dual_stays_with_every_feature_toward_pt_br(bare, _full):
    assert convert(bare, "br_1971", "ao1990-br") == bare


@pytest.mark.xfail(strict=True, reason="desacordo#116: the dual step writes sector where setor is valid")
@pytest.mark.parametrize("bare, _full", PT_DUALS)
def test_a_valid_bare_dual_stays_with_every_feature_toward_pt_pt(bare, _full):
    assert convert(bare, "pt_1973", "ao1990-pt") == bare
