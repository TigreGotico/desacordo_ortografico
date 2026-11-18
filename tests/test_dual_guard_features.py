"""The c/p form of a dual stays as written whatever ``features`` run.

Owner ruling for duals: "Where both forms are valid in the target variety, write the c/p
form ... 'valid in the target variety' is decided by the official vocabulary: VOLP (ABL)
for pt-BR, VOP (ILTEC, Portal da Língua Portuguesa, RCM 8/2011) for pt-PT ... A VOLP pair
joined by 'cf.' with different glosses is two words, not a dual (ótica/óptica,
seção/secção)."

The dual choice of ``silent-cp`` (pt-PT) and ``volp`` (pt-BR) writes the c/p form. A
caller that runs a subset of the features must not lose it: every other feature leaves
the c/p form of a dual as written. The hold reaches no other word: a cf. pair, a row
for one reading and a variant that is not c/p convert as before. Each expected value
comes from the vocabulary entry quoted beside it.
"""
import pytest

from desacordo_ortografico import FEATURES, convert

#: the feature sets of the tugaphone spelling step (pt group, br group)
PT_STEP = frozenset({"1911-word-map", "trema", "ao-map-consonant", "base-iv", "initial-sc",
                     "ao-map-diacritic"})
BR_STEP = frozenset({"1911-word-map", "base-iv", "initial-sc", "ptbr-divergence", "hyphen-lexical"})


def _rewritten(text, target, step, source="etymological", without=frozenset()):
    """The feature sets, and their outputs, that rewrite ``text``: every feature, ``step``,
    and each feature on its own, all without the features in ``without``."""
    sets = [FEATURES - without, step - without, *({f} for f in sorted(FEATURES - without))]
    return [(sorted(f), out) for f in sets
            if (out := convert(text, source, target, features=f)) != text]


# VOP lemma 117204: "setor - nome masculino ... variante AO : sector"
# VOP lemma 48215: "carácter - nome masculino ... Portugal ... variante AO de : caráter"
# VOP lemma 106786: "acupunctura - nome feminino ... variante AO de : acupuntura"
@pytest.mark.parametrize("source", ["etymological", "pt_1973"])
@pytest.mark.parametrize("text", ["o sector e os sectores", "o carácter", "a acupunctura"])
def test_a_pt_pt_dual_keeps_the_consonant_under_any_features(text, source):
    assert _rewritten(text, "ao1990-pt", PT_STEP, source) == []


@pytest.mark.parametrize("source", ["etymological", "br_1971", "ao1990-pt"])
@pytest.mark.parametrize("text", [
    "o facto",  # VOLP: fato s.m. | facto s.m.
    "o contacto",  # VOLP: contato s.m. | contacto s.m.
    "os contactos",  # the regular plural of the contacto row
    "o corrupto",  # VOLP: corruto adj. s.m. | corrupto adj. s.m.
    "a conjectura",  # VOLP: conjetura s.f. | conjectura s.f.
    "o cetro",  # VOLP: cetro s.m.; no ceptro
])
def test_a_volp_c_p_form_stays_toward_pt_br_without_the_volp_feature(text, source):
    assert _rewritten(text, "ao1990-br", BR_STEP, source, without={"volp"}) == []


# VOLP: conjetura s.f. | conjectura s.f.; epilético adj. s.m. | epiléptico adj. s.m.;
# infecioso (ô) adj. ... | infeccioso (ô) adj. Only the c/p form is held, so the bare
# pt-PT form still takes the consonant on the divergence edge.
@pytest.mark.parametrize("features", [FEATURES, FEATURES - {"volp"}, BR_STEP])
def test_a_pt_pt_bare_form_of_a_volp_dual_takes_the_consonant(features):
    assert convert("a conjetura epilética", "ao1990-pt", "ao1990-br", features=features) \
        == "a conjectura epiléptica"
    assert convert("os infeciosos", "ao1990-pt", "ao1990-br", features=features) == "os infecciosos"


@pytest.mark.parametrize("features", [FEATURES, BR_STEP])
@pytest.mark.parametrize("text, expected", [
    # VOLP: seção s.f. "corte", etc.; cf. secção | secção s.f. "parcela"; cf. seção
    ("a secção de perdidos e achados", "a seção de perdidos e achados"),
    # VOLP: oticista s.2g. "pessoa versada em ótica"; cf. opticista | opticista adj. s.2g.
    # "pessoa versada em óptica"; cf. oticista
    ("o oticista", "o opticista"),
    # VOLP: registo s.m.; registro s.m. (not a c/p pair)
    ("o registo", "o registro"),
])
def test_the_hold_reaches_no_word_outside_a_c_p_dual(text, expected, features):
    assert convert(text, "pt_1973", "ao1990-br", features=features) == expected


def test_a_row_for_one_reading_is_not_held():
    # VOLP: fatura s.f. | factura s.f.; faturar v., and no row for facturar
    assert convert("Ele factura muito.", "pt_1973", "ao1990-br") == "Ele fatura muito."


def test_a_european_form_the_volp_lists_for_fewer_readings_takes_its_row():
    # VOLP: retângulo adj. s.m. | rectângulo adj.; the noun in every row
    assert convert("o rectângulo", "pt_1973", "ao1990-br") == "o retângulo"


def test_the_1911_accent_guess_still_reads_a_held_word():
    # VOLP: eletrodo (ô) s.m. | electrodo (ô) s.m.; elétrodo s.m. | eléctrodo s.m.
    assert convert("electrodos", "etymological", "ao1990-br") == "eléctrodos"
