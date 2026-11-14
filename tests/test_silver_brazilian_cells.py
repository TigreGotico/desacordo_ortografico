"""The Brazilian cells of the silver corpus write Brazilian spellings.

br_1971 is the pre-1990 Brazilian norm. Its sources, in order: the ABL Formulário
Ortográfico of 1943 (with Lei 5.765/1971), whose rule 18 registers both forms of the
words it lists and whose rule 16 fixes one form ("diretor ... ótimo ... e não ...
director ... optimo"); then the Brazilian headword of the Dicionário Priberam page in the
view before the AO1990. Rule 15.ª, OBSERVAÇÃO, writes the preterite ending -amos without
the accent.

ao1990-br follows the ABL Vocabulário Ortográfico da Língua Portuguesa (VOLP), then the
Priberam Brazilian view after the AO1990, then Michaelis. Where the VOLP lists both forms
of one word with the same part of speech, the cell writes the c/p form.

Where a source registers both forms, the cell writes the c/p form (owner ruling on dual
spellings). Each test names the entry it pins.
"""
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

import pytest

BENCHMARK = Path(__file__).parent.parent / "benchmark"
TOKEN = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[-'][0-9A-Za-zÀ-ɏ]+)*")
BRAZILIAN = ("br_1971", "ao1990-br")
PLAIN = str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc")
POS = re.compile(r"(?<![\w.])(s\.m\.|s\.f\.|s\.2g\.|adj\.|v\.|adv\.|top\.)")


def _rows():
    with (BENCHMARK / "silver_corpus.jsonl").open(encoding="utf-8") as f:
        return {row["id"]: row for row in map(json.loads, f)}


def _tsv(name):
    with (BENCHMARK / name).open(encoding="utf-8") as f:
        next(f)
        return [line.rstrip("\n").split("\t") for line in f]


def _tokens(row, cell):
    return [t.lower() for t in TOKEN.findall(row["cells"][cell])]


@pytest.mark.parametrize("row_id,cell,word", [
    # Formulário 1943, 18: "contacto e contato"; VOLP: contato s.m. | contacto s.m.
    ("p02-015", "br_1971", "contacto"),
    ("p02-015", "ao1990-br", "contacto"),
    # Formulário 1943, 18: "secção e seção"; the VOLP splits them with "cf.", and
    # Michaelis seção 6 is a section of a shop
    ("p09-056", "br_1971", "secção"),
    ("p09-056", "ao1990-br", "seção"),
    # Priberam facto (Brazil before the AO1990: fato); VOLP: fato s.m. | facto s.m.
    ("p02-018", "br_1971", "fato"),
    ("p02-018", "ao1990-br", "facto"),
    # Formulário 1943, 16: "ótimo ... e não ... optimo"; VOLP: ótimo adj. s.m. | óptimo adj. s.m.
    ("p04-001", "br_1971", "ótimo"),
    ("p04-001", "ao1990-br", "óptimo"),
    # Priberam sector (Brazil before the AO1990: setor); VOLP: setor s.m. | sector s.m.
    ("p03-034", "br_1971", "setor"),
    ("p03-034", "ao1990-br", "sector"),
    # Priberam detectar (Brazil before the AO1990: detectar); VOLP: detectar v. | detetar v.
    ("p03-020", "br_1971", "detectou"),
    ("p03-020", "ao1990-br", "detectou"),
    # Formulário 1943, 18: "infecção e infeção"; VOLP: infecção s.f. | infeção s.f.
    ("p04-003", "br_1971", "infecção"),
    ("p04-003", "ao1990-br", "infecção"),
    # Priberam electrónico (Brazil before the AO1990: eletrônico); VOLP: eletrônico adj. |
    # electrônico adj.
    ("p10-008", "br_1971", "eletrônico"),
    ("p10-008", "ao1990-br", "electrônico"),
    ("p10-052", "ao1990-br", "electrônica"),
    # Priberam recto (Brazil before the AO1990: reto); VOLP: reto adj. s.m. | recto adj. s.m.,
    # the adjective in "filosofia reta"
    ("p08-028", "br_1971", "reta"),
    ("p08-028", "ao1990-br", "recta"),
    # VOLP: elétron s.m. | eléctron s.m.
    ("p01-024", "ao1990-br", "eléctron"),
    # Priberam óptica (Brazil before the AO1990: óptica); VOLP: óptica s.f. "ciência da
    # visão"; cf. ótica ("ciência da audição")
    ("p04-013", "br_1971", "óptica"),
    ("p04-013", "ao1990-br", "óptica"),
])
def test_brazilian_cell_writes_the_source_form(row_id, cell, word):
    assert word in _tokens(_rows()[row_id], cell)


def test_the_c_p_form_keeps_the_brazilian_circumflex():
    """VOLP: eletrônico adj. | electrônico adj. The aligned European electrónica must not
    give these rows the acute of the European spelling."""
    rows = _rows()
    for row_id in ("p10-008", "p10-052", "p10-082"):
        for cell in BRAZILIAN:
            assert not [t for t in _tokens(rows[row_id], cell) if t.startswith(("electró", "eletró"))]


def _c_p_pairs(row, cell):
    """Tokens of the cell aligned with a pt_1973 token that is the same word plus one c/p."""
    european = _tokens(row, "pt_1973")
    tokens = _tokens(row, cell)
    if len(tokens) != len(european):
        return []
    found = []
    for t, e in zip(tokens, european):
        a, b = t.translate(PLAIN), e.translate(PLAIN)
        if len(b) == len(a) + 1 and any(b[:i] + b[i + 1:] == a for i in range(len(b)) if b[i] in "cp"):
            found.append((t, e))
    return found


def test_every_bare_form_against_a_european_c_p_form_is_decided():
    """A Brazilian token that drops the c/p of its pt_1973 word either changes by a table
    line or stays by a line of variety_keeps.tsv that names its source for that cell."""
    keeps = {(c, t, e) for c, t, e, _reason in _tsv("variety_keeps.tsv")}
    gaps = sorted({(row_id, cell, t, e) for row_id, row in _rows().items() for cell in BRAZILIAN
                   for t, e in _c_p_pairs(row, cell) if (cell, t, e) not in keeps})
    assert gaps == []


def test_br_1971_writes_amos_without_the_accent():
    found = [(row_id, t) for row_id, row in _rows().items()
             for t in _tokens(row, "br_1971") if t.endswith("ámos")]
    assert found == []


def test_no_row_holds_an_undecidable_token():
    drops = {(cell, token) for cell, token, _reason in _tsv("variety_drops.tsv")}
    found = [(row_id, cell, t) for row_id, row in _rows().items()
             for cell in BRAZILIAN for t in _tokens(row, cell) if (cell, t) in drops]
    assert found == []


def test_every_line_names_its_source():
    """A br_1971 line cites the Formulário or the Priberam view before the AO1990, never the VOLP."""
    for cell, token, _european, fix, _rows_named, source in _tsv("variety_fixes.tsv"):
        assert cell in BRAZILIAN
        assert token != fix
        if cell == "br_1971":
            assert source.startswith("Formulário 1943, ") or (
                source.startswith("Priberam ") and "before the AO1990" in source), source
        else:
            assert source.startswith(("VOLP: ", "Priberam ", "Michaelis: ")), source
    for cell, _token, _european, reason in _tsv("variety_keeps.tsv"):
        allowed = ("Formulário 1943, ", "Priberam ", "no source: ") if cell == "br_1971" else \
            ("VOLP: ", "Priberam ", "Michaelis: ", "no source: ")
        assert reason.startswith(allowed), reason


def _one_c_p_apart(bare, cp):
    """True when cp is bare with one c or p inserted, or with mp written for n (accents kept)."""
    if any(cp[:i] + cp[i + 1:] == bare for i in range(len(cp)) if cp[i] in "cp"):
        return True
    return any(cp == bare[:i] + "mp" + bare[i + 1:] for i in range(len(bare)) if bare[i] == "n")


def test_every_c_p_line_changes_one_consonant_and_no_accent():
    """Deleting the consonant from the longer form gives the shorter form, accents included."""
    for cell, token, _european, fix, _rows_named, _source in _tsv("variety_fixes.tsv"):
        if len(fix) != len(token) and "-" not in fix + token:
            longer, shorter = (fix, token) if len(fix) > len(token) else (token, fix)
            assert _one_c_p_apart(shorter, longer), (cell, token, fix)


def _entry(text):
    """Headword and parts of speech of a VOLP entry text such as 'reto adj. s.m.'."""
    head = text.split()[0].lower()
    return head, set(POS.findall(re.split(r'[;"]|cf\.', text[len(head):])[0]))


def test_a_volp_line_pairs_one_lemma_with_one_part_of_speech():
    """VOLP: reta s.f. and recto adj. s.m. are two words, so no line pairs them."""
    for cell, _token, _european, _fix, _rows_named, source in _tsv("variety_fixes.tsv"):
        m = re.match(r"VOLP: ([^|;]+?) \| ([^|;]+?)(?:;|$)", source)
        if cell != "ao1990-br" or not m:
            continue
        (hb, pb), (hc, pc) = _entry(m.group(1)), _entry(m.group(2))
        assert _one_c_p_apart(hb, hc) or _one_c_p_apart(hc, hb), source
        assert pb & pc, source


def _apply_module():
    spec = importlib.util.spec_from_file_location("apply_variety_fixes",
                                                  BENCHMARK / "apply_variety_fixes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _apply(sentence, european, row_id="t0"):
    apply = _apply_module()
    row = {"id": row_id, "cells": {"pt_1973": european, "br_1971": sentence, "ao1990-br": sentence}}
    apply.fix_row(row, apply.load_table(), Counter())
    return row["cells"]


def test_apply_writes_the_c_p_form_and_amos_only_in_br_1971():
    """Priberam detectar (Brazil before the AO1990: detectar); Formulário 1943, 18:
    "infecção e infeção"; VOLP: detectar v. | detetar v.; infecção s.f. | infeção s.f."""
    cells = _apply("Detetou as infeções e visitámos.", "Detectou as infecções e visitámos.")
    assert cells["br_1971"] == "Detectou as infecções e visitamos."
    assert cells["ao1990-br"] == "Detectou as infecções e visitámos."


def test_apply_reads_the_word_from_the_european_cell():
    """Priberam facto (Brazil before the AO1990: fato); VOLP: facto s.m. | fato s.m. The
    fact takes the c/p form in ao1990-br only; the suit (pt_1973 fato) is another word."""
    cells = _apply("O fato é claro.", "O facto é claro.")
    assert (cells["br_1971"], cells["ao1990-br"]) == ("O fato é claro.", "O facto é claro.")
    assert _apply("O fato é azul.", "O fato é azul.")["ao1990-br"] == "O fato é azul."


def test_apply_writes_a_formulario_dual_and_keeps_a_formulario_single_form():
    """Formulário 1943, 18: "tecto e teto"; 16: "ótimo ... e não ... optimo". The VOLP
    lists teto and no tecto, and lists ótimo and óptimo."""
    cells = _apply("O teto é ótimo.", "O tecto é óptimo.")
    assert cells["br_1971"] == "O tecto é ótimo."
    assert cells["ao1990-br"] == "O teto é óptimo."


def test_apply_keeps_a_single_brazilian_form():
    """VOLP: ação s.f., with no acção; seção s.f. "corte", etc. for a section of a shop.
    Priberam acção (Brazil before the AO1990: ação); Formulário 1943, 18: "secção e seção"."""
    cells = _apply("A ação da seção.", "A acção da secção.")
    assert cells["ao1990-br"] == "A ação da seção."
    assert cells["br_1971"] == "A ação da secção."


def test_apply_splits_the_noun_reta_from_the_adjective():
    """VOLP: reta s.f., with no recta, for the noun; reto adj. s.m. | recto adj. s.m. for
    the adjective in p08-028."""
    assert _apply("A reta final.", "A recta final.")["ao1990-br"] == "A reta final."
    assert _apply("Uma obra reta.", "Uma obra recta.", "p08-028")["ao1990-br"] == "Uma obra recta."


def test_apply_writes_mp_where_the_sources_list_it():
    """Formulário 1943, 18: "sumptuoso e suntuoso"; VOLP: suntuoso adj. | sumptuoso adj.;
    VOLP: perempto adj., with no perento."""
    cells = _apply("O palácio suntuoso.", "O palácio sumptuoso.")
    assert (cells["br_1971"], cells["ao1990-br"]) == ("O palácio sumptuoso.", "O palácio sumptuoso.")
    assert _apply("Um prazo perento.", "Um prazo perempto.")["ao1990-br"] == "Um prazo perempto."


def test_apply_writes_the_pre_1990_circumflex_in_br_1971():
    """Priberam bebé (Brazil before the AO1990: bebê); Formulário 1943, 43, 1.ª. The VOLP
    lists bebé and bebê (AO1990, Base VIII 1 a), so ao1990-br keeps the token."""
    cells = _apply("O bebé dorme.", "O bebé dorme.")
    assert (cells["br_1971"], cells["ao1990-br"]) == ("O bebê dorme.", "O bebé dorme.")


def test_apply_drops_a_row_with_an_undecidable_token():
    apply = _apply_module()
    row = {"cells": {"br_1971": "A detetiva chegou.", "ao1990-br": "A detetiva chegou."}}
    assert apply.undecidable(row, apply.load_drops())
