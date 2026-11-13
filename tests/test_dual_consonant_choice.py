"""A dual cell of an AO1990 word map gives pt-PT the consonant and pt-BR no consonant.

AO1990 Base IV 1º c makes both forms valid: "Conservam-se ou eliminam-se
facultativamente, quando se proferem numa pronúncia culta, quer geral, quer
restritamente, ou então quando oscilam entre a prolação e o emudecimento: aspecto e
aspeto, cacto e cato, caracteres e carateres, dicção e dição; facto e fato, sector e
setor, ceptro e cetro, concepção e conceção, corrupto e corruto, recepção e receção".
Base IV 2º does the same for the m of mn: "o m da sequência mn, em amnistia, ...
omnímodo, omnipotente, omnisciente, etc.".

The choice of one form per variety is an owner ruling: where the tugalex map lists two
AO1990 forms, a pt-PT target takes the form with the consonant and a pt-BR target the
form without it, in both directions. Derivatives follow, so a text never mixes forms.
"""
import pytest

from desacordo_ortografico import convert

# pt-PT form, pt-BR form. Each pair is one dual cell of the tugalex pt-PT map, or its
# plural (Cunha & Cintra cap. 8: -es after r, -s after a vowel).
PAIRS = [("sector", "setor"), ("sectores", "setores"), ("carácter", "caráter"),
         ("acupunctura", "acupuntura"), ("acupuncturas", "acupunturas")]


@pytest.mark.parametrize("pt, _br", PAIRS)
def test_pt_pt_target_keeps_the_consonant(pt, _br):
    assert convert(f"o {pt}", "pt_1973", "ao1990-pt") == f"o {pt}"


@pytest.mark.parametrize("pt, br", PAIRS)
def test_pt_br_target_drops_the_consonant(pt, br):
    assert convert(f"o {pt}", "pt_1973", "ao1990-br") == f"o {br}"
    assert convert(f"o {pt}", "ao1990-pt", "ao1990-br") == f"o {br}"


@pytest.mark.parametrize("pt, br", PAIRS)
def test_pt_br_to_pt_pt_gains_the_consonant(pt, br):
    assert convert(f"o {br}", "ao1990-br", "ao1990-pt") == f"o {pt}"


@pytest.mark.parametrize("pt, br", [("sector", "setor"), ("carácter", "caráter"),
                                    ("acupunctura", "acupuntura")])
def test_ao1990_pt_form_without_consonant_goes_back(pt, br):
    # both forms are valid AO1990 pt-PT; the pre-AO1990 spelling has the consonant
    assert convert(f"o {br}", "ao1990-pt", "pt_1973") == f"o {pt}"


def test_espectador_takes_the_pt_pt_consonant():
    # dual cell espectador -> espectador, espetador
    assert convert("o espectador", "pt_1973", "ao1990-pt") == "o espectador"
    assert convert("o espetador", "ao1990-br", "ao1990-pt") == "o espectador"
    assert convert("os espectadores", "ao1990-br", "ao1990-pt") == "os espectadores"


def test_espectador_keeps_the_curated_pt_br_form():
    # data/base_iv.json lists pt-BR espectador as a word of its own norm; the feminine
    # follows it
    assert convert("o espectador e a espectadora", "pt_1973", "ao1990-br") == "o espectador e a espectadora"


def test_caracteres_is_the_plural_in_both_varieties():
    # Cunha & Cintra cap. 8, Observação 1.ª: "O plural de caráter (escrito carácter na
    # ortografia portuguesa) é, tanto no Brasil como em Portugal, caracteres"
    assert convert("o carácter e os caracteres", "pt_1973", "ao1990-pt") == "o carácter e os caracteres"
    assert convert("o caráter e os caracteres", "ao1990-br", "ao1990-pt") == "o carácter e os caracteres"
    assert convert("o carácter e os caracteres", "pt_1973", "ao1990-br") == "o caráter e os caracteres"


def test_dual_and_derivative_take_the_same_form():
    assert convert("o sector sectorial", "pt_1973", "ao1990-pt") == "o sector sectorial"
    assert convert("o sector sectorial", "pt_1973", "ao1990-br") == "o setor setorial"
    assert convert("os setores setoriais", "ao1990-br", "ao1990-pt") == "os sectores sectoriais"


def test_brazilian_accent_still_applies():
    # the dual gives espetrofotómetro, and the pt-BR nasal-vowel rule writes ô
    assert convert("espectrofotómetro", "ao1990-pt", "ao1990-br") == "espetrofotômetro"


# contrato (a contract) and retrato (a portrait) are words of their own beside the duals
# contracto (contracted) and retracto (a retraction), so they never gain the c.
@pytest.mark.parametrize("word", ["contrato", "retrato"])
def test_word_of_its_own_does_not_gain_the_consonant(word):
    assert convert(f"o {word}", "ao1990-br", "ao1990-pt") == f"o {word}"
    assert convert(f"o {word}", "ao1990-pt", "pt_1973") == f"o {word}"


def test_word_of_its_own_still_loses_it_toward_pt_br():
    assert convert("contracto", "pt_1973", "ao1990-br") == "contrato"


# Dual cells of the tugalex pt-BR map: liquefacto -> liquefacto, liquefato; co-factor ->
# cofator, cofactor; omnilíngue -> omnilingue, onilingue (Base IV 2º).
@pytest.mark.parametrize("old, br", [("liquefacto", "liquefato"), ("co-factor", "cofator"),
                                     ("omnilíngue", "onilingue")])
def test_pt_br_map_dual_drops_the_consonant(old, br):
    assert convert(old, "br_1971", "ao1990-br") == br


def test_pt_br_map_dual_gains_it_toward_pt_pt():
    # the pt-PT map has no row for liquefacto, so the pt-BR cell decides
    assert convert("liquefato", "ao1990-br", "ao1990-pt") == "liquefacto"


def test_pt_br_dual_that_is_a_pre_ao1990_spelling_goes_back_as_written():
    assert convert("liquefato", "ao1990-br", "br_1971") == "liquefato"
