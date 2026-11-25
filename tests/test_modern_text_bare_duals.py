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

With every feature, convert() writes the c/p form of a dual (the dual ruling).
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


@pytest.mark.parametrize("bare, full", BR_DUALS)
def test_every_feature_writes_the_form_with_the_consonant_toward_pt_br(bare, full):
    assert convert(bare, "br_1971", "ao1990-br") == full


@pytest.mark.parametrize("bare, full", PT_DUALS)
def test_every_feature_writes_the_form_with_the_consonant_toward_pt_pt(bare, full):
    assert convert(bare, "pt_1973", "ao1990-pt") == full


@pytest.mark.parametrize("bare, full", BR_DUALS)
def test_the_dual_choice_stays_inside_volp_and_silent_cp_toward_pt_br(bare, full):
    """Adding `volp` to the group makes the choice, so the pin above is not vacuous."""
    assert convert(bare, "br_1971", "ao1990-br", features=BR_GROUP | {"volp"}) == full


@pytest.mark.parametrize("bare, full", PT_DUALS)
def test_the_dual_choice_stays_inside_volp_and_silent_cp_toward_pt_pt(bare, full):
    assert convert(bare, "pt_1973", "ao1990-pt", features=PT_GROUP | {"silent-cp"}) == full
