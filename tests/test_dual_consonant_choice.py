"""Where both forms are valid in the target variety, the converter writes the consonant.

AO1990 Base IV 1º c makes both forms valid: "Conservam-se ou eliminam-se
facultativamente, quando se proferem numa pronúncia culta, quer geral, quer
restritamente, ou então quando oscilam entre a prolação e o emudecimento: aspecto e
aspeto, cacto e cato, caracteres e carateres, dicção e dição; facto e fato, sector e
setor, ceptro e cetro, concepção e conceção, corrupto e corruto, recepção e receção".
Base IV 2º does the same for the m of mn: "o m da sequência mn, em amnistia, ...
omnímodo, omnipotente, omnisciente, etc.".

The choice of the form with the consonant is an owner ruling. A dual cell of the
tugalex AO1990 map of the target variety lists the two valid forms. For pt-BR the ABL
VOLP decides each word that data/volp_ao1990_br.tsv holds before the tugalex map does
(tests/test_volp_ao1990_br.py): the VOLP lists only cofator. A word with one valid form
takes that form. Every route that does not end at an AO1990 target converts as on
origin/dev.
"""
import csv
from pathlib import Path

import pytest
from tugalex import TugaLexicon

from desacordo_ortografico import convert
from desacordo_ortografico.convert import FEATURES
from desacordo_ortografico.lexicon import get_lexicon

_TUGA = TugaLexicon()
_VOLP = get_lexicon().ao_br_volp


def _cells(table):
    """(old form, form with the consonant, form without it) of each dual cell."""
    for old, forms in table.items():
        cell = {f.lower().strip() for f in forms if f.strip()}
        if len(cell) == 2:
            bare, full = sorted(cell, key=len)
            yield old.lower(), full, bare


# contrato (a contract) and retrato (a portrait) are words of their own beside the duals
# contracto (contracted) and retracto (a retraction), so they never gain the c.
HOMOGRAPHS = {"contrato", "retrato"}
PT_CELLS = [c for c in _cells(_TUGA.ao_pt) if c[2] not in HOMOGRAPHS]
BR_CELLS = sorted({(full, bare) for _old, full, bare in _cells(_TUGA.ao_br)})


# infeto is also a form of infetar, which has one pt-PT spelling (VOP lemma 37066), so
# infecto converts to infeto (tests/test_dual_verb_forms.py).
VERB_FORMS = {"infeto"}


def test_every_pt_pt_dual_cell_takes_the_consonant_toward_pt_pt():
    wrong = [(old, full, convert(old, "pt_1973", "ao1990-pt")) for old, full, bare in PT_CELLS
             if convert(old, "pt_1973", "ao1990-pt") != (bare if bare in VERB_FORMS else full)]
    assert wrong == []


@pytest.mark.parametrize("full, bare", BR_CELLS)
def test_every_pt_br_dual_cell_takes_the_consonant_toward_pt_br(full, bare):
    # VOLP: cofator adj. s.m.; no cofactor
    expected = _VOLP.get(bare, full)
    assert convert(bare, "ao1990-pt", "ao1990-br") == expected
    assert convert(full, "ao1990-pt", "ao1990-br") == expected


# Dual cells of the tugalex pt-PT map (sector -> setor, sector; carácter -> caráter,
# carácter; acupunctura -> acupuntura, acupunctura), and their plurals (Cunha & Cintra
# cap. 8: -es after r, -s after a vowel).
PT_DUALS = [("sector", "setor"), ("sectores", "setores"), ("carácter", "caráter"),
            ("acupunctura", "acupuntura"), ("acupuncturas", "acupunturas")]


@pytest.mark.parametrize("full, _bare", PT_DUALS)
def test_pt_pt_dual_keeps_the_consonant(full, _bare):
    assert convert(f"o {full}", "pt_1973", "ao1990-pt") == f"o {full}"
    assert convert(f"O {full.upper()}", "pt_1973", "ao1990-pt") == f"O {full.upper()}"


@pytest.mark.parametrize("full, bare", PT_DUALS)
def test_pt_pt_dual_gains_the_consonant_from_pt_br(full, bare):
    assert convert(f"o {bare}", "ao1990-br", "ao1990-pt") == f"o {full}"


def test_espectador_takes_the_pt_pt_consonant():
    # dual cell espectador -> espectador, espetador
    assert convert("o espectador", "pt_1973", "ao1990-pt") == "o espectador"
    assert convert("o espetador", "ao1990-br", "ao1990-pt") == "o espectador"
    assert convert("os espectadores", "ao1990-br", "ao1990-pt") == "os espectadores"


def test_caracteres_is_the_plural_in_both_varieties():
    # Base IV 1º c names the pair: "caracteres e carateres"
    assert convert("o carácter e os caracteres", "pt_1973", "ao1990-pt") == "o carácter e os caracteres"
    assert convert("o caráter e os carateres", "ao1990-br", "ao1990-pt") == "o carácter e os caracteres"


def test_al_and_el_plurals_take_the_consonant():
    # dual cells sectorial -> setorial, sectorial and perfectível -> perfetível,
    # perfectível; -al makes -ais and -vel makes -veis
    assert convert("os setores setoriais perfetíveis", "ao1990-br", "ao1990-pt") \
        == "os sectores sectoriais perfectíveis"


def test_pt_br_dual_plural_takes_the_consonant():
    # -es after r (Cunha & Cintra cap. 8), and -ção makes -ções
    assert convert("os liquefatores e as liquefações", "ao1990-pt", "ao1990-br") \
        == "os liquefactores e as liquefacções"


def test_unstressed_il_plural_takes_the_consonant():
    # Priberam, táctil: "Plural: táteis. Plural: tácteis" and "Dupla grafia pelo Acordo
    # Ortográfico de 1990: tátil ou táctil"
    assert convert("o tátil e os táteis", "ao1990-br", "ao1990-pt") == "o táctil e os tácteis"


def test_adjective_datilar_plural_takes_the_consonant():
    # Aulete, datilar: "adj. || dactilar"; Dicio, datilar: "Relativo ou pertencente aos dedos ... Var: dactilar."
    assert (convert("a impressão datilar e as impressões datilares", "ao1990-br", "ao1990-pt")
            == "a impressão dactilar e as impressões dactilares")


# The plural of each ending that the dual cells have, written out per ending: -s after a
# vowel and -es after r and z (Cunha & Cintra cap. 8, pp. 191-218), -ção to -ções, -al
# to -ais, -vel and the unstressed -il of táctil to -eis (Priberam, táctil: "Plural:
# tácteis"), the pair caracteres, carateres (Base IV 1º c), and the adjective
# datilar, dactilar (Aulete, datilar: "adj. || dactilar") with -es. Verbs and adverbs in
# -mente have no plural. Every dual cell in -s of the tugalex map is a plural or a feminine
# plural in -as, -os, -es or -ais (sectoriais, insectívoras, subsectores), and the map lists
# that plural as a cell of its own, so a cell in -s takes no plural here. A singular in -s
# has a plural of its own (país, países) or an invariable one (o lápis, os lápis). The test
# raises for a cell in -s outside those four endings; it cannot tell a singular such as
# atlas or cais from a plural, which is safe only while every such cell has its singular
# in the same CSV.
_PLURAL_ENDINGS = [("ção", "ções"), ("al", "ais"), ("vel", "veis"), ("til", "teis"),
                   ("or", "ores"), ("z", "zes"), ("a", "as"), ("e", "es"), ("o", "os")]
_SPECIAL_PLURALS = {"carácter": "caracteres", "caráter": "carateres",
                    "dactilar": "dactilares", "datilar": "datilares"}


def _expected_plural(word):
    if word in _SPECIAL_PLURALS:
        return _SPECIAL_PLURALS[word]
    if word.endswith(("ar", "er", "ir", "mente")):
        return None
    if word.endswith("s"):
        assert word.endswith(("as", "os", "es", "ais")), f"no plural class for {word}"
        return None
    assert not word.endswith("ão") or word.endswith("ção"), word
    for singular, plural in _PLURAL_ENDINGS:
        if word.endswith(singular):
            return word[:len(word) - len(singular)] + plural
    raise AssertionError(f"no plural class for {word}")


def _csv_cells(path):
    """(form without the consonant, form with it) of each row with two AO1990 forms in a
    tugalex CSV, read with the csv module."""
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))[1:]
    for _old, new in rows:
        forms = {w.strip().lower() for w in new.split(",") if w.strip()}
        if len(forms) == 2:
            yield tuple(sorted(forms, key=len))


@pytest.mark.parametrize("table, path, cell", [
    ("ao_pt_dual_full", _TUGA.ao_pt_path, ("setor", "sector")),
    ("ao_br_dual_full", _TUGA.ao_br_path, ("cofator", "cofactor")),
])
def test_the_maps_hold_the_dual_cells(table, path, cell):
    # every dual cell of the CSV and the plural of each, and nothing else
    expected = {}
    for bare, full in _csv_cells(path):
        if bare in HOMOGRAPHS:
            continue
        for key, value in ((bare, full), (_expected_plural(bare), _expected_plural(full))):
            if key is not None and value is not None:
                assert expected.setdefault(key, value) == value, key
    if table == "ao_pt_dual_full":
        # Verb forms of infetar and intercetar, which have one pt-PT spelling (VOP lemmas
        # 37066 and 191891). Their plurals infetos and intercetos stay in the table.
        for word in ("infeto", "interceto"):
            expected.pop(word)
    assert expected[cell[0]] == cell[1]
    assert getattr(get_lexicon(), table) == expected


@pytest.mark.parametrize("table, cells", [("ao_pt_dual_full", PT_CELLS),
                                          ("ao_br_dual_full", list(_cells(_TUGA.ao_br)))])
def test_every_dual_cell_plural_takes_the_consonant(table, cells):
    duals = getattr(get_lexicon(), table)
    wrong, plurals = [], 0
    for _old, full, bare in cells:
        pair = _expected_plural(bare), _expected_plural(full)
        if pair == (None, None):
            assert bare + "es" not in duals and bare + "s" not in duals
            continue
        plurals += 1
        if duals.get(pair[0]) != pair[1]:
            wrong.append((bare, full, pair, duals.get(pair[0])))
    assert wrong == []
    assert plurals > len(cells) / 2


def test_the_rule_is_the_silent_cp_feature():
    without = FEATURES - {"silent-cp"}
    # origin/dev output, with or without the feature
    assert convert("o setor", "ao1990-br", "ao1990-pt", features=without) == "o setor"
    assert convert("o setor", "ao1990-br", "ao1990-pt") == "o sector"


def test_each_element_of_a_compound_takes_the_consonant():
    assert convert("o setor e o setor-chave", "ao1990-br", "ao1990-pt") == "o sector e o sector-chave"
    # a cell that is itself a compound converts as a whole
    assert convert("a eletro-óptica", "ao1990-pt", "ao1990-br") == "a electro-óptica"


@pytest.mark.parametrize("word", sorted(HOMOGRAPHS))
def test_word_of_its_own_does_not_gain_the_consonant(word):
    assert convert(f"o {word}", "ao1990-br", "ao1990-pt") == f"o {word}"
    assert convert(f"o {word}", "pt_1973", "ao1990-pt") == f"o {word}"


# Every other route converts as on origin/dev (a3ef145). The expected values below are
# origin/dev output.
def test_route_to_pt_br_converts_pt_pt_duals_as_on_dev():
    # VOLP: setor (ô) s.m. | sector (ô) s.m.; caráter s.m.; pl. caracteres; no carácter
    assert convert("o sector e o carácter", "pt_1973", "ao1990-br") == "o sector e o caráter"
    assert convert("a acupunctura", "pt_1973", "br_1971") == "a acupuntura"


# origin/dev output of both forms of each pt-BR dual cell, from AO1990 pt-PT to br_1971
BR_1971_DEV = [("anti-ictérico", "antiictérico"), ("anti-itérico", "anti-itérico"),
               ("codialecto", "codialecto"), ("codialeto", "co-dialecto"),
               ("cofactor", "cofactor"), ("cofator", "co-fator"),
               ("dactilozoide", "dactilozóide"), ("datilozoide", "datilozoide"),
               ("electro-óptica", "electro-óptica"), ("eletro-óptica", "eletroóptica"),
               ("electro-óptico", "electro-óptico"), ("eletro-óptico", "eletroóptico"),
               ("liquefactivo", "liquefactivo"), ("liquefativo", "liquefactivo"),
               ("liquefacto", "liquefato"), ("liquefato", "liquefato"),
               ("liquefactor", "liquefactor"), ("liquefator", "liquefactor"),
               ("liquefacção", "liquefacção"), ("liquefação", "liquefacção"),
               ("omnilingue", "omnilíngue"), ("onilingue", "onilingue")]


@pytest.mark.parametrize("word, dev", BR_1971_DEV)
def test_pt_br_dual_toward_br_1971_converts_as_on_dev(word, dev):
    assert convert(word, "ao1990-pt", "br_1971") == dev


def test_pt_br_dual_toward_pt_pt_converts_as_on_dev():
    assert convert("liquefato", "ao1990-br", "ao1990-pt") == "liquefato"
    assert convert("co-dialecto", "br_1971", "ao1990-pt") == "codialeto"


# tests/data/ptbr_dual_dev_outputs.tsv holds the origin/dev output of every form of every
# pt-PT dual cell, from each European source to each pt-BR norm. Only the forms of a
# pt-BR dual cell toward ao1990-br differ, by the rule above. Toward ao1990-br, the VOLP
# then decides each word of the origin/dev output that it holds, or each element of a
# compound. The file leaves out the
# rows where the Brazilian form that Priberam gives differs from the origin/dev output
# (tests/test_silent_cp_listed_words.py), and the rows of contracto and retracto toward
# pt-BR: Priberam gives contrato and retrato, but these are also the words contract and
# portrait, so no pt -> br row can hold them.
_FIXTURE = Path(__file__).parent / "data" / "ptbr_dual_dev_outputs.tsv"
_BR_DUAL_FORMS = {f for _old, full, bare in _cells(_TUGA.ao_br) for f in (full, bare)}


def _dev_rows():
    with open(_FIXTURE, encoding="utf-8") as f:
        next(f)
        for line in f:
            word, src, dst, out = line.rstrip("\n").split("\t")
            if not (dst == "ao1990-br" and word in _BR_DUAL_FORMS):
                yield word, src, dst, out


def _volp_form(out, dst):
    if dst != "ao1990-br":
        return out
    return _VOLP.get(out) or "-".join(_VOLP.get(p, p) for p in out.split("-"))


def test_pt_pt_dual_toward_pt_br_converts_as_on_dev():
    rows = list(_dev_rows())
    assert len(rows) == 2825
    wrong = [(w, s, d, out, convert(w, s, d)) for w, s, d, out in rows
             if convert(w, s, d) != _volp_form(out, d)]
    assert wrong == []
