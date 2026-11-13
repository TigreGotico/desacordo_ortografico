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
in the target variety takes that form. Toward pt-BR, a dual of the pt-PT map takes
Brazil's form of the pair: the tugalex pt-BR map row, else the data/base_iv.json pt-BR
form, else the one form of the pair the tugalex Brazilian word list (rjx) holds, else
the form the pt-PT cell lists first.
"""
import pytest

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
def test_pt_br_dual_as_written_from_ao1990_pt(word):
    # both forms are valid AO1990 pt-BR, so a pt-PT text keeps the form it has
    assert convert(word, "ao1990-pt", "ao1990-br") == word


def test_pt_br_dual_that_is_a_pre_ao1990_spelling_goes_back_as_written():
    assert convert("liquefacto", "ao1990-br", "br_1971") == "liquefacto"


def test_pt_br_dual_gains_the_consonant_toward_pt_pt():
    # the pt-PT map has no row for liquefacto, so the pt-BR cell decides
    assert convert("liquefato", "ao1990-br", "ao1990-pt") == "liquefacto"


# Dual cells of the pt-PT map only, toward pt-BR. Brazil's form comes from Brazilian data.
# tugalex word list rjx holds one form of the pair: setor (not sector), espectro (not
# espetro), expectativa (not expetativa), conector (not conetor).
@pytest.mark.parametrize("pt_form, br", [("sector", "setor"), ("setor", "setor"),
                                         ("espectro", "espectro"), ("espetro", "espectro"),
                                         ("expetativa", "expectativa"), ("conetor", "conector")])
def test_pt_pt_dual_toward_pt_br_takes_the_brazilian_word_list_form(pt_form, br):
    assert convert(pt_form, "ao1990-pt", "ao1990-br") == br


# rjx holds both forms of carácter/caráter, característica/caraterística and
# acupunctura/acupuntura, so the form the tugalex pt-PT cell lists first decides.
@pytest.mark.parametrize("pt_form, br", [("carácter", "caráter"), ("acupunctura", "acupuntura"),
                                         ("caraterística", "característica")])
def test_pt_pt_dual_toward_pt_br_with_both_forms_listed(pt_form, br):
    assert convert(pt_form, "ao1990-pt", "ao1990-br") == br


def test_pt_pt_dual_toward_pt_br_takes_the_pt_br_map_row():
    # tugalex pt-BR map: perfeccionista -> perfecionista
    assert convert("perfeccionista", "ao1990-pt", "ao1990-br") == "perfecionista"


def test_pt_pt_dual_toward_pt_br_takes_base_iv_form():
    # data/base_iv.json dual: {"pt": "espetador", "br": "espectador"}
    assert convert("o espetador e os espetadores", "ao1990-pt", "ao1990-br") == "o espectador e os espectadores"


@pytest.mark.parametrize("src", ["pt_1973", "etymological"])
def test_pt_pt_dual_toward_pt_br_from_older_sources(src):
    assert convert("o sector e os sectores", src, "ao1990-br") == "o setor e os setores"
    assert convert("o carácter e a acupunctura", src, "ao1990-br") == "o caráter e a acupuntura"
    assert convert("o espectro e a expectativa", src, "ao1990-br") == "o espectro e a expectativa"
    assert convert("a característica", src, "ao1990-br") == "a característica"


def test_pt_pt_dual_toward_br_1971():
    assert convert("o sector", "pt_1973", "br_1971") == "o setor"


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
