"""A word that the official vocabulary of the target variety gives stays as written,
whatever ``features`` run.

Owner ruling for duals: "Where both forms are valid in the target variety, write the c/p
form ... 'valid in the target variety' is decided by the official vocabulary: VOLP (ABL)
for pt-BR, VOP (ILTEC, Portal da Língua Portuguesa, RCM 8/2011) for pt-PT ... A VOLP pair
joined by 'cf.' with different glosses is two words, not a dual (ótica/óptica,
seção/secção)."

The c/p form of a dual is written by the dual choice of ``silent-cp`` (pt-PT) and
``volp`` (pt-BR). Every other feature leaves a valid word as written, so a caller that
runs a subset of the features never loses the consonant of a dual and never rewrites
one word into another. Each expected value comes from the vocabulary entry quoted
beside it.
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
    "o corrupto",  # VOLP: corruto adj. s.m. | corrupto adj. s.m.
    "o cetro",  # VOLP: cetro s.m.; no ceptro
    "a conjetura",  # VOLP: conjetura s.f. | conjectura s.f.
])
def test_a_volp_form_stays_toward_pt_br_without_the_volp_feature(text, source):
    assert _rewritten(text, "ao1990-br", BR_STEP, source, without={"volp"}) == []


def test_the_volp_feature_still_writes_the_consonant_of_a_dual():
    # VOLP: conjetura s.f. | conjectura s.f.; epilético adj. s.m. | epiléptico adj. s.m.
    assert convert("a conjetura epilética", "br_1971", "ao1990-br") == "a conjectura epiléptica"
    assert convert("a conjetura epilética", "br_1971", "ao1990-br", features=BR_STEP) \
        == "a conjetura epilética"


@pytest.mark.parametrize("source", ["etymological", "br_1971", "ao1990-pt"])
def test_the_verb_cato_stays(source):
    # VOLP: cato adj. s.m. | cacto s.m.; cato is also the first person of catar
    assert _rewritten("Eu cato as folhas.", "ao1990-br", BR_STEP, source) == []


@pytest.mark.parametrize("source", ["etymological", "br_1971", "pt_1973"])
@pytest.mark.parametrize("text", [
    "a secção",  # VOLP: secção s.f. "parcela"; cf. seção, sessão, ceção e cessão
    "a seção",  # VOLP: seção s.f. "corte", etc.; cf. ceção, cessão, secção e sessão
    "a óptica",  # VOLP: óptica s.f. "ciência da visão"; cf. ótica
    "a ótica",  # VOLP: ótica s.f. "ciência da audição"; cf. óptica
])
def test_a_cf_pair_stays_toward_pt_br(text, source):
    assert _rewritten(text, "ao1990-br", BR_STEP, source) == []


@pytest.mark.parametrize("text", [
    "a amígdala",  # VOLP: amígdala s.f.
    "o quotidiano",  # VOLP: quotidiano adj. s.m.
    "o aspeto",  # VOLP: aspeto s.m. | aspecto s.m. (the volp feature writes aspecto)
    "o subtil",  # VOLP: subtil adj.2g. s.m.
    "o súbdito",  # VOLP: súbdito adj. s.m.
    "o registo",  # VOLP: registo s.m.
])
def test_a_pt_br_word_the_divergence_table_holds_stays(text):
    assert convert(text, "ao1990-pt", "ao1990-br", features=BR_STEP) == text
    expected = "o aspecto" if text == "o aspeto" else text
    assert convert(text, "ao1990-pt", "ao1990-br") == expected


def test_a_european_form_the_volp_lists_for_fewer_readings_takes_its_row():
    # VOLP: retângulo adj. s.m. | rectângulo adj.; the noun in every row
    assert convert("o rectângulo", "pt_1973", "ao1990-br") == "o retângulo"
