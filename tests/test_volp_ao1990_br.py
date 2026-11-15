"""A conversion to ao1990-br writes the form the ABL VOLP gives each word it holds.

The ABL Vocabulário Ortográfico da Língua Portuguesa (VOLP) is the official vocabulary
of Brazil. ``data/volp_ao1990_br.tsv`` quotes the VOLP entry of each word. Where the
VOLP lists both forms of one word, the converter writes the form with the consonant
(owner ruling: "if both forms are valid, keep the one with the consonant"). Where it
lists one form, the converter writes that form. Two entries that point to each other
with "cf." and carry different glosses are two words, so neither form becomes the
other. Each expected value below comes from the VOLP entry quoted beside it.
"""
import csv
import re
from pathlib import Path

import pytest

from desacordo_ortografico import FEATURES, convert
from desacordo_ortografico.lexicon import get_lexicon

SOURCES = ("br_1971", "ao1990-pt", "etymological")


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("bare, full", [
    ("fato", "facto"),  # VOLP: fato s.m. | facto s.m.
    ("setor", "sector"),  # VOLP: setor (ô) s.m. | sector (ô) s.m.
    ("ótimo", "óptimo"),  # VOLP: ótimo adj. s.m. interj. | óptimo adj. s.m. interj.
    ("liquefação", "liquefacção"),  # VOLP: liquefação (u ou ü) s.f. | liquefacção (u ou ü) s.f.
])
def test_a_volp_dual_takes_the_consonant(source, bare, full):
    # a pt-PT fato is the suit, see test_a_pt_pt_bare_form_that_is_another_word_stays
    if not (source == "ao1990-pt" and bare == "fato"):
        assert convert(f"o {bare}", source, "ao1990-br") == f"o {full}"
    assert convert(f"o {full}", source, "ao1990-br") == f"o {full}"


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("bare, full", [
    ("aceção", "acepção"),  # VOLP: acepção s.f.; no aceção
    ("acetor", "aceptor"),  # VOLP: aceptor (ô) adj. s.m.; no acetor
])
def test_a_single_volp_form_with_the_consonant(source, bare, full):
    assert convert(f"a {bare}", source, "ao1990-br") == f"a {full}"


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("word", [
    "cofator",  # VOLP: cofator adj. s.m.; no cofactor
    "calefator",  # VOLP: calefator (ô) adj. s.m.; no calefactor
])
def test_a_single_volp_form_without_the_consonant(source, word):
    assert convert(f"o {word}", source, "ao1990-br") == f"o {word}"


@pytest.mark.parametrize("source", ("ao1990-pt", "pt_1973"))
def test_a_pt_pt_bare_form_that_is_another_word_stays(source):
    """pt-PT writes facto for the fact (base_iv.json dual facto/fato; VOP facto), so a
    pt-PT fato is the suit, another word. VOLP: fato s.m. | facto s.m. decides the fact."""
    assert convert("Comprei um fato novo.", source, "ao1990-br") == "Comprei um fato novo."
    assert convert("Os fatos novos.", source, "ao1990-br") == "Os fatos novos."
    assert convert("O facto é claro.", source, "ao1990-br") == "O facto é claro."


def test_a_brazilian_bare_form_takes_the_volp_dual():
    """VOLP: fato s.m. | facto s.m. A Brazilian fato is the fact."""
    assert convert("o fato", "br_1971", "ao1990-br") == "o facto"


def test_a_pt_pt_bare_form_of_the_same_word_takes_the_volp_dual():
    """pt-PT drops the p of óptimo (AO1990 Base IV 1º b: "ótimo"), so a pt-PT ótimo is the
    same word. VOLP: ótimo adj. s.m. interj. | óptimo adj. s.m. interj."""
    assert convert("ótimo", "ao1990-pt", "ao1990-br") == "óptimo"


@pytest.mark.parametrize("source, full, bare", [
    ("ao1990-pt", "cofactor", "cofator"),  # VOLP: cofator adj. s.m.; no cofactor
    ("etymological", "projecto", "projeto"),  # VOLP: projeto s.m.; no projecto
])
def test_a_single_volp_form_rejects_the_form_with_the_consonant(source, full, bare):
    assert convert(f"o {full}", source, "ao1990-br") == f"o {bare}"


@pytest.mark.parametrize("source", ("br_1971", "ao1990-pt"))
def test_the_regular_plural_follows_its_row(source):
    """VOLP: cofator adj. s.m.; no cofactor. The plural adds -es after r (Cunha & Cintra
    cap. 8), and the VOLP lists no cofactores."""
    assert convert("os cofatores e os cofactores", source, "ao1990-br") == "os cofatores e os cofatores"


def test_a_plural_the_quote_gives_is_not_derived():
    """VOLP: caráter s.m.; pl. caracteres; no carácter."""
    assert convert("o caráter e os caracteres", "br_1971", "ao1990-br") == "o caráter e os caracteres"


def test_a_quote_with_a_sense_note_rejects_no_form():
    """VOLP: eletromecânica s.f.; no electromecânica. The row notes "not the adjective
    electromecânico", so the quote rejects no form, and the feminine adjective stays."""
    assert convert("a engenharia electromecânica", "ao1990-pt", "ao1990-br") == "a engenharia electromecânica"


@pytest.mark.parametrize("word", [
    # VOLP: ótica s.f. "ciência da audição"; cf. óptica | óptica s.f. "ciência da visão"; cf. ótica
    "ótica", "óptica",
    # VOLP: ótico adj. "relativo a audição"; cf. óptico | óptico adj. s.m. "relativo a visão"; cf. ótico
    "ótico", "óptico",
    # VOLP: oticista s.2g. "pessoa versada em ótica"; cf. opticista | opticista adj. s.2g.
    # "pessoa versada em óptica"; cf. oticista
    "oticista", "opticista",
])
def test_a_cf_pair_is_two_words(word):
    assert convert(f"a {word}", "br_1971", "ao1990-br") == f"a {word}"


def test_seção_and_secção_are_two_words():
    """VOLP: seção s.f. "corte", etc.; cf. secção | secção s.f. "parcela"; cf. seção."""
    assert convert("a seção e a secção", "br_1971", "ao1990-br") == "a seção e a secção"


def test_case_and_compounds_follow_the_volp():
    """VOLP: setor (ô) s.m. | sector (ô) s.m.; ótimo adj. s.m. interj. | óptimo adj. s.m. interj."""
    assert convert("O Setor é ÓTIMO.", "br_1971", "ao1990-br") == "O Sector é ÓPTIMO."
    assert convert("o setor-chave", "br_1971", "ao1990-br") == "o sector-chave"


def test_the_volp_rule_is_the_volp_feature():
    without = FEATURES - {"volp"}
    assert convert("o cofator", "br_1971", "ao1990-br", features=without) == "o cofactor"
    assert convert("o cofator", "br_1971", "ao1990-br") == "o cofator"
    assert convert("a aceção", "br_1971", "ao1990-br", features={"volp"}) == "a acepção"


def test_other_targets_ignore_the_volp():
    """The VOLP is the vocabulary of pt-BR AO1990 only."""
    assert convert("o setor e a aceção", "br_1971", "ao1990-pt") == convert(
        "o setor e a aceção", "br_1971", "ao1990-pt", features=FEATURES - {"volp"})
    assert convert("o fato", "br_1971", "br_1943") == "o fato"


def test_a_row_for_named_sentences_is_left_out():
    """VOLP: elétrico adj. s.m. | eléctrico adj. The silver corpus splits the tram from the
    adjective by row, so the converter holds no decision for elétrico."""
    assert "elétrico" not in get_lexicon().ao_br_volp


with (Path(__file__).parent.parent / "desacordo_ortografico" / "data" / "volp_ao1990_br.tsv").open(
        encoding="utf-8", newline="") as _f:
    ROWS = list(csv.DictReader(_f, delimiter="\t", quoting=csv.QUOTE_NONE))


def test_every_row_quotes_its_source():
    for row in ROWS:
        assert row["source"].startswith(("VOLP: ", "Priberam ", "no source: ")), row


def test_a_two_words_row_quotes_cf_both_ways():
    """A row is two words when the VOLP points from each form to the other with "cf."."""
    for row in ROWS:
        other = row["form"] if row["form"] != row["token"] else row["european"]
        mutual = f"cf. {row['token']}" in row["source"] and f"cf. {other}" in row["source"]
        assert (row["pair"] == "two words") == mutual, row


def test_rows_for_every_sentence_agree():
    forms = {}
    for row in ROWS:
        if row["rows"] == "*" and row["pair"] == "one word":
            forms.setdefault(row["token"], set()).add(row["form"])
    assert {t: f for t, f in forms.items() if len(f) > 1} == {}


def _adds_the_consonant(bare, full):
    """True when full is bare with one c or p inserted, or with mp written for n."""
    if any(full[:i] + full[i + 1:] == bare for i in range(len(full)) if full[i] in "cp"):
        return True
    return any(full == bare[:i] + "mp" + bare[i + 1:] for i in range(len(bare)) if bare[i] == "n")


def test_a_listed_word_takes_its_row_form():
    """No derived form (a rejected form or a plural) overrides a row for every sentence."""
    volp = get_lexicon().ao_br_volp
    wrong = [row for row in ROWS if row["rows"] == "*" and row["pair"] == "one word"
             and volp[row["token"]] != row["form"]]
    assert wrong == []


def test_a_dual_row_writes_the_consonant():
    """A row that quotes two VOLP entries of one word with the same part of speech and no
    note writes the form with the consonant."""
    dual = re.compile(r"VOLP: \S+ ([^|;\"]+) \| \S+ \1$")
    checked = 0
    for row in ROWS:
        if dual.match(row["source"]):
            checked += 1
            assert _adds_the_consonant(row["token"], row["form"]), row
    assert checked > 300
