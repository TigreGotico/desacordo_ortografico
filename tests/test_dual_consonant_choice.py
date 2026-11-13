"""Where both forms are valid in the target variety, the converter writes the consonant.

AO1990 Base IV 1º c makes both forms valid: "Conservam-se ou eliminam-se
facultativamente, quando se proferem numa pronúncia culta, quer geral, quer
restritamente, ou então quando oscilam entre a prolação e o emudecimento: aspecto e
aspeto, cacto e cato, caracteres e carateres, dicção e dição; facto e fato, sector e
setor, ceptro e cetro, concepção e conceção, corrupto e corruto, recepção e receção".
Base IV 2º does the same for the m of mn: "o m da sequência mn, em amnistia, ...
omnímodo, omnipotente, omnisciente, etc.".

The choice of the form with the consonant is an owner ruling. A dual cell of the
tugalex map of the target variety lists the two valid forms. A word with one valid form
in the target variety takes that form. Toward pt-BR, a dual of the pt-PT map only
converts as on origin/dev.
"""
from pathlib import Path

import pytest
from tugalex import TugaLexicon

from desacordo_ortografico import convert

# Dual cells of the tugalex pt-PT map (sector -> setor, sector; carácter -> caráter,
# carácter; acupunctura -> acupuntura, acupunctura), and their plurals (Cunha & Cintra
# cap. 8: -es after r, -s after a vowel).
PT_DUALS = [("sector", "setor"), ("sectores", "setores"), ("carácter", "caráter"),
            ("acupunctura", "acupuntura"), ("acupuncturas", "acupunturas")]


@pytest.mark.parametrize("full, _bare", PT_DUALS)
def test_pt_pt_dual_keeps_the_consonant(full, _bare):
    assert convert(f"o {full}", "pt_1973", "ao1990-pt") == f"o {full}"


@pytest.mark.parametrize("full, bare", PT_DUALS)
def test_pt_pt_dual_gains_the_consonant_from_pt_br(full, bare):
    assert convert(f"o {bare}", "ao1990-br", "ao1990-pt") == f"o {full}"


@pytest.mark.parametrize("full, bare", [("sector", "setor"), ("carácter", "caráter"),
                                        ("acupunctura", "acupuntura")])
def test_ao1990_pt_form_without_consonant_goes_back(full, bare):
    # both forms are valid AO1990 pt-PT; the pre-AO1990 spelling has the consonant
    assert convert(f"o {bare}", "ao1990-pt", "pt_1973") == f"o {full}"


def test_espectador_takes_the_pt_pt_consonant():
    # dual cell espectador -> espectador, espetador
    assert convert("o espectador", "pt_1973", "ao1990-pt") == "o espectador"
    assert convert("o espetador", "ao1990-br", "ao1990-pt") == "o espectador"
    assert convert("os espectadores", "ao1990-br", "ao1990-pt") == "os espectadores"


def test_caracteres_is_the_plural_in_both_varieties():
    # Cunha & Cintra cap. 8, Observação 1.ª: "O plural de caráter (escrito carácter na
    # ortografia portuguesa) é, tanto no Brasil como em Portugal, caracteres"
    assert convert("o carácter e os caracteres", "pt_1973", "ao1990-pt") == "o carácter e os caracteres"
    assert convert("o caráter e os caracteres", "ao1990-br", "ao1990-pt") == "o carácter e os caracteres"
    assert convert("os caracteres", "pt_1973", "ao1990-br") == "os caracteres"


def test_dual_and_derivative_take_the_same_form():
    assert convert("o sector sectorial", "pt_1973", "ao1990-pt") == "o sector sectorial"
    assert convert("os setores setoriais", "ao1990-br", "ao1990-pt") == "os sectores sectoriais"


# Dual cells of the tugalex pt-BR map: liquefato -> liquefacto, liquefato; liqüefação ->
# liquefacção, liquefação; co-dialeto -> codialecto, codialeto; co-factor -> cofator,
# cofactor; onilíngüe -> omnilingue, onilingue (Base IV 2º).
@pytest.mark.parametrize("old, full", [("liquefato", "liquefacto"), ("liqüefação", "liquefacção"),
                                       ("co-dialeto", "codialecto"), ("co-factor", "cofactor"),
                                       ("onilíngüe", "omnilingue")])
def test_pt_br_dual_keeps_the_consonant(old, full):
    assert convert(old, "br_1971", "ao1990-br") == full


@pytest.mark.parametrize("word", ["liquefacto", "liquefato"])
def test_pt_br_dual_takes_the_consonant_from_ao1990_pt(word):
    assert convert(word, "ao1990-pt", "ao1990-br") == "liquefacto"


def test_pt_br_dual_that_is_a_pre_ao1990_spelling_goes_back_as_written():
    assert convert("liquefacto", "ao1990-br", "br_1971") == "liquefacto"


def test_pt_br_dual_gains_the_consonant_toward_pt_pt():
    # the pt-PT map has no row for liquefacto, so the pt-BR cell decides
    assert convert("liquefato", "ao1990-br", "ao1990-pt") == "liquefacto"


# Toward pt-BR, a dual of the pt-PT map only converts as on origin/dev (a3ef145): the
# pt-PT dual choice does not speak for Brazil. tests/data/ptbr_dual_dev_outputs.tsv holds
# the origin/dev output of every form of every pt-PT dual cell, from each European source
# to each pt-BR norm. The forms of a pt-BR dual cell take its consonant form instead, and
# pre-1911 contracto reads as the noun (below).
_FIXTURE = Path(__file__).parent / "data" / "ptbr_dual_dev_outputs.tsv"
_BR_DUAL_FORMS = {f for old, forms in TugaLexicon().ao_br.items() if len(set(forms)) > 1
                  for f in (old.lower(), *(f.lower() for f in forms))}


def _dev_rows():
    with open(_FIXTURE, encoding="utf-8") as f:
        next(f)
        for line in f:
            word, src, dst, out = line.rstrip("\n").split("\t")
            if word not in _BR_DUAL_FORMS and not (src == "etymological" and word == "contracto"):
                yield word, src, dst, out


def test_pt_pt_dual_toward_pt_br_converts_as_on_dev():
    rows = list(_dev_rows())
    assert len(rows) == 3022
    wrong = [(w, s, d, out, convert(w, s, d)) for w, s, d, out in rows if convert(w, s, d) != out]
    assert wrong == []


# On the route to pt-BR, the pt-PT step takes the first form of a pt-PT dual cell
# (sector -> setor, sector) and the plain c/p rule, so the pt-PT map evidence of an
# inflection does not drop a consonant Brazil pronounces (detectado: the pt-PT map gives
# detectar -> detetar).
def test_route_to_pt_br_takes_the_first_form():
    assert convert("o sector e o carácter", "pt_1973", "ao1990-br") == "o setor e o caráter"
    assert convert("a acupunctura", "pt_1973", "br_1971") == "a acupuntura"


def test_route_to_pt_br_keeps_brazilian_consonants():
    assert convert("detectado e perceptíveis", "pt_1973", "ao1990-br") == "detectado e perceptíveis"
    assert convert("detectado e perceptíveis", "pt_1973", "ao1990-pt") == "detetado e percetíveis"


@pytest.mark.parametrize("word", ["espectro", "expectativa", "característica", "conector",
                                  "telespectador"])
def test_pt_pt_dual_from_ao1990_pt_stays_toward_pt_br(word):
    assert convert(word, "ao1990-pt", "ao1990-br") == word


def test_pt_pt_dual_toward_pt_br_takes_base_iv_form():
    # data/base_iv.json dual: {"pt": "espetador", "br": "espectador"}
    assert convert("o espetador e os espetadores", "ao1990-pt", "ao1990-br") == "o espectador e os espectadores"


def test_pt_br_form_of_a_pt_pt_dual_stays_toward_pt_pt():
    # ptbr_br2pt leaves out espectador -> espetador: pt-PT keeps the consonant of the dual
    # cell espectador -> espectador, espetador
    assert convert("o espectador", "ao1990-br", "ao1990-pt") == "o espectador"


def test_brazilian_accent_applies_to_a_pt_pt_dual():
    # espectrofotómetro is a dual of the pt-PT map only, so pt-BR keeps the c, and the
    # pt-BR nasal-vowel rule writes ô
    assert convert("espectrofotómetro", "ao1990-pt", "ao1990-br") == "espectrofotômetro"


# contrato (a contract) and retrato (a portrait) are words of their own beside the duals
# contracto (contracted) and retracto (a retraction), so they never gain the c.
@pytest.mark.parametrize("word", ["contrato", "retrato"])
def test_word_of_its_own_does_not_gain_the_consonant(word):
    assert convert(f"o {word}", "ao1990-br", "ao1990-pt") == f"o {word}"
    assert convert(f"o {word}", "ao1990-pt", "pt_1973") == f"o {word}"


# Before 1911, contracto spelled both the noun "contract" (contrato from 1911) and the
# adjective "contracted" (contracto, an AO1990 dual). The noun is far more frequent.
@pytest.mark.parametrize("dst", ["ao1990-pt", "ao1990-br", "pt_1973"])
def test_pre_1911_contracto_reads_as_the_noun(dst):
    assert convert("o contracto e os contractos", "etymological", dst) == "o contrato e os contratos"


def test_pt_1973_contracto_is_the_adjective():
    assert convert("contracto", "pt_1973", "ao1990-pt") == "contracto"
