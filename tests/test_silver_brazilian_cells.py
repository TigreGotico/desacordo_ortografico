"""The Brazilian cells of the silver corpus write Brazilian spellings.

br_1971 is the pre-1990 Brazilian norm. Its sources, in order: the ABL Formulário
Ortográfico of 1943 (with Lei 5.765/1971), whose rule 18 registers both forms of the
words it lists and whose rule 16 fixes one form ("diretor ... ótimo ... e não ...
director ... optimo"); then the ABL Pequeno Vocabulário Ortográfico of 1943, whose entry
registers a second spelling after a colon ("setor (ô), s. m.: sector."); then the
Brazilian headword of the Dicionário Priberam page in the view before the AO1990, when the
page shows a spelling change. Rule 43, 15.ª, OBSERVAÇÃO, writes the preterite ending -amos
without the accent.

ao1990-br follows the ABL Vocabulário Ortográfico da Língua Portuguesa (VOLP), then the
Priberam Brazilian view after the AO1990. Where the VOLP lists both forms
of one word with the same part of speech, the cell writes the c/p form. A Priberam page
with one spelling in all four views records no spelling change, so it decides nothing.

Where a source registers both forms, the cell writes the c/p form (owner ruling on dual
spellings). A personal or place name stays as written unless a source names it. Each test
names the entry it pins.
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
    # Formulário 1943, 18: "secção e seção"; VOLP: seção s.f. "corte", etc.; cf. secção |
    # secção s.f. "parcela"; cf. seção. A section of a shop is the "corte, etc." entry.
    ("p09-056", "br_1971", "secção"),
    ("p09-056", "ao1990-br", "seção"),
    # Vocabulário 1943, p. 635: "fato, s. m.", with no facto; VOLP: fato s.m. | facto s.m. "O
    # fato de" means a fact; the Brazilian cells reword the sentence, so no token aligns with facto.
    ("p05-046", "br_1971", "fato"),
    ("p05-046", "ao1990-br", "facto"),
    ("p05-082", "br_1971", "fato"),
    ("p05-082", "ao1990-br", "facto"),
    # Vocabulário 1943, p. 635: "fato, s. m.", with no facto; VOLP: fato s.m. | facto s.m.
    ("p02-018", "br_1971", "fato"),
    ("p02-018", "ao1990-br", "facto"),
    # Formulário 1943, 16: "ótimo ... e não ... optimo"; VOLP: ótimo adj. s.m. | óptimo adj. s.m.
    ("p04-001", "br_1971", "ótimo"),
    ("p04-001", "ao1990-br", "óptimo"),
    # Vocabulário 1943, p. 1177: "setor (ô), s. m.: sector."; VOLP: setor s.m. | sector s.m.
    ("p03-034", "br_1971", "sector"),
    ("p03-034", "ao1990-br", "sector"),
    # Vocabulário 1943, p. 478: "detectar, v.", with no detetar; VOLP: detectar v. | detetar v.
    ("p03-020", "br_1971", "detectou"),
    ("p03-020", "ao1990-br", "detectou"),
    # Formulário 1943, 18: "infecção e infeção"; VOLP: infecção s.f. | infeção s.f.
    ("p04-003", "br_1971", "infecção"),
    ("p04-003", "ao1990-br", "infecção"),
    # Vocabulário 1943, p. 511: "electrônico, adj.: eletrônico."; VOLP: eletrônico adj. |
    # electrônico adj.
    ("p10-008", "br_1971", "electrônico"),
    ("p10-008", "ao1990-br", "electrônico"),
    ("p10-052", "ao1990-br", "electrônica"),
    # Priberam recto (Brazil before the AO1990: reto); VOLP: reto adj. s.m. | recto adj. s.m.,
    # the adjective in "filosofia reta"
    ("p08-028", "br_1971", "reta"),
    ("p08-028", "ao1990-br", "recta"),
    # VOLP: elétron s.m. | eléctron s.m.
    ("p01-024", "ao1990-br", "eléctron"),
    # Vocabulário 1943, p. 964: "óptica, s. f.: ótica."; VOLP: óptica s.f. "ciência da
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
    keeps = {}
    for c, t, e, rows_named, _reason in _tsv("variety_keeps.tsv"):
        keeps.setdefault((c, t, e), set()).update(rows_named.split(","))
    gaps = sorted({(row_id, cell, t, e) for row_id, row in _rows().items() for cell in BRAZILIAN
                   for t, e in _c_p_pairs(row, cell)
                   if not keeps.get((cell, t, e), set()) & {row_id, "*"}})
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
    """A br_1971 line cites the Formulário, a page of the 1943 vocabulary or the Priberam
    view before the AO1990, never the VOLP."""
    for cell, token, _european, fix, _rows_named, source in _tsv("variety_fixes.tsv"):
        assert cell in BRAZILIAN
        assert token != fix
        if cell == "br_1971":
            assert re.match(r"Formulário 1943, |Vocabulário 1943, p\. \d+", source) or (
                source.startswith("Priberam ") and "before the AO1990" in source), source
        else:
            assert source.startswith(("VOLP: ", "Priberam ")), source
    for cell, _token, _european, _rows_named, reason in _tsv("variety_keeps.tsv"):
        allowed = ("Formulário 1943, ", "Vocabulário 1943, p. ", "Priberam ", "no source: ") \
            if cell == "br_1971" else ("VOLP: ", "Priberam ", "no source: ")
        assert reason.startswith(allowed), reason


PRIBERAM_VIEWS = re.compile(r"Priberam [^()]+ \(Brazil before the AO1990: ([^,]+), after: ([^;]+); "
                            r"Portugal before: ([^,]+), after: ([^)]+)\)")


def test_a_br_1971_priberam_citation_shows_a_spelling_change():
    """A Priberam page decides br_1971 only when its spelling changes with the AO1990 in
    Brazil or in Portugal, or when Brazil and Portugal wrote two spellings before it.
    Priberam produto shows produto in all four views, so it decides nothing."""
    cited = [(token, source) for cell, token, _e, _y, _r, source in _tsv("variety_fixes.tsv")
             if cell == "br_1971" and source.startswith("Priberam ")]
    cited += [(token, reason) for cell, token, _e, _r, reason in _tsv("variety_keeps.tsv")
              if cell == "br_1971" and reason.startswith("Priberam ")]
    assert len(cited) > 400
    for token, source in cited:
        m = PRIBERAM_VIEWS.match(source)
        assert m, source
        brazil_before, brazil_after, portugal_before, portugal_after = m.groups()
        assert len({brazil_before, brazil_after, portugal_before, portugal_after}) > 1, (token, source)


@pytest.mark.parametrize("sentence,european,expected", [
    # Vocabulário 1943, p. 355: "clichê, s. m.: adapt. do fr. cliché."
    ("Um cliché gasto.", "Um cliché gasto.", "Um clichê gasto."),
    # Vocabulário 1943, p. 687: "gêiser, s. m.: adapt. do ingl. geyser."
    ("O géiser jorrou.", "O géiser jorrou.", "O gêiser jorrou."),
    # Vocabulário 1943, p. 400: "corruto, adj.: corrupto." registers both spellings, and
    # the dual ruling writes the c/p form (d18971).
    ("O sistema corruto de distribuição.", "O sistema corrupto de distribuição.",
     "O sistema corrupto de distribuição."),
    # Vocabulário 1943, p. 1177: "setor (ô), s. m.: sector." Priberam sector (Brazil before
    # the AO1990: setor) kept setor; the vocabulary comes first.
    ("O setor público.", "O sector público.", "O sector público."),
    # Vocabulário 1943, p. 381: "conjetura, s. f.", with no conjectura. Priberam conjectura
    # (Brazil before the AO1990: conjectura) wrote conjectura; the vocabulary comes first.
    ("Uma conjetura falsa.", "Uma conjectura falsa.", "Uma conjetura falsa."),
    # Vocabulário 1943, p. 1069: "prospetiva, s. f.", with no prospectiva.
    ("A prospetiva do mercado.", "A prospectiva do mercado.", "A prospetiva do mercado."),
    # Vocabulário 1943, p. 796: "jacto, s. m.: jato."
    ("Um jato de água.", "Um jacto de água.", "Um jacto de água."),
    # The vocabulary has no comitê or comité between comissurante and comitente (p. 371),
    # and no other source records the vowel, so the token stays.
    ("O comité reuniu.", "O comité reuniu.", "O comité reuniu."),
    # Vocabulário 1943, p. 1065: "produto, s. m.", with no producto.
    ("Um produto novo.", "Um producto novo.", "Um produto novo."),
])
def test_br_1971_takes_the_spelling_of_the_1943_vocabulary(sentence, european, expected):
    assert _apply(sentence, european)["br_1971"] == expected


def test_a_br_1971_word_the_1943_vocabulary_registers_is_not_residual():
    """The vocabulary decides these words, so no "no source" keep line names them."""
    keeps = {(cell, token): reason for cell, token, _european, _rows_named, reason in _tsv("variety_keeps.tsv")}
    for token in ("produto", "produtos", "produtor"):
        assert keeps[("br_1971", token)].startswith("Vocabulário 1943, p. 1065: produt"), token
    assert keeps[("br_1971", "comité")].startswith("no source: ")


def test_a_personal_name_stays_as_written():
    """Formulário 1943, 39 puts names under the rules for common words, and rule 16 writes
    Otávia; no ao1990-br source names Otávia, so the token stays."""
    cells = _apply("Ontem a Otávia chegou.", "Ontem a Octávia chegou.", "d07020")
    assert (cells["br_1971"], cells["ao1990-br"]) == ("Ontem a Otávia chegou.", "Ontem a Otávia chegou.")
    for cell, token, *_rest in _tsv("variety_fixes.tsv"):
        assert token != "otávia", cell


def test_a_place_name_stays_and_the_common_word_changes():
    """VOLP: ártico adj. | árctico adj. covers the adjective, not the Arctic."""
    assert _apply("Viajou para o Ártico.", "Viajou para o Árctico.")["ao1990-br"] == "Viajou para o Ártico."
    assert _apply("O gelo ártico.", "O gelo árctico.")["ao1990-br"] == "O gelo árctico."


def test_apply_keeps_the_tram_and_writes_the_c_p_adjective():
    """VOLP: elétrico adj. s.m. | eléctrico adj. lists eléctrico only as an adjective, so
    the noun (a tram) in d05064 and the plural noun in d05139 stay."""
    tram = _apply("Apanhou o elétrico.", "Apanhou o eléctrico.", "d05064")
    assert tram["ao1990-br"] == "Apanhou o elétrico."
    trams = _apply("Ciclistas e elétricos.", "Ciclistas e eléctricos.", "d05139")
    assert trams["ao1990-br"] == "Ciclistas e elétricos."
    adjective = _apply("O carro elétrico.", "O carro eléctrico.", "d01067")
    assert adjective["ao1990-br"] == "O carro eléctrico."


@pytest.mark.parametrize("row_id,european,sentence,kept,rejected", [
    # The Italian dish name "bistecca alla fiorentina", not the Portuguese word (VOLP: bisteca
    # s.f., with no bistecca).
    ("d03149", "Em Florença, a bistecca alla fiorentina chegou à mesa imensa e suculenta.",
     "Em Florença, a bistecca alla fiorentina chegou à mesa imensa e suculenta.", "bistecca", "bisteca"),
    # VOLP: elétrico adj. s.m. | eléctrico adj. The noun "linha de elétrico" is a tram line,
    # and the VOLP lists eléctrico only as an adjective.
    ("d05210", "A exactidão na previsão da procura evitou sobredimensionar a nova linha de eléctrico.",
     "A exatidão na previsão da procura evitou sobredimensionar a nova linha de elétrico.",
     "elétrico", "eléctrico"),
    # VOLP: seção s.f. "corte", etc.; cf. secção | secção s.f. "parcela"; cf. seção. Each row
    # names a department or a division, the "corte, etc." entry.
    ("d13248", "A detecção de toxicidade impediu que mensagens ofensivas chegassem à secção de comentários.",
     "A deteção de toxicidade impediu que mensagens ofensivas chegassem à secção de comentários.",
     "seção", "secção"),
    ("d14892", "O exactor anexou a factura ao dossiê e remeteu o processo à secção de desembaraço aduaneiro.",
     "O exator anexou a fatura ao dossiê e remeteu o processo à secção de desembaraço aduaneiro.",
     "seção", "secção"),
    ("d17327", "A secção de violas foi reforçada com três novos músicos este ano.",
     "A secção de violas foi reforçada com três novos músicos este ano.", "seção", "secção"),
    ("d17959", "O objecto esquecido no banco do vagão foi entregue à secção de perdidos e achados.",
     "O objeto esquecido no banco do vagão foi entregue à secção de perdidos e achados.", "seção", "secção"),
    # The VOLP lists neither retor nor rector (it lists reitor (ô) s.m. and rétor s.m.).
    # Priberam rector shows rector in all four views, so it decides nothing, and reitor is
    # another word.
    ("d22099", "O rector da universidade abriu solenemente o ano lectivo.",
     "O retor da universidade abriu solenemente o ano letivo.", "retor", "rector"),
])
def test_apply_follows_the_row_decision_in_ao1990_br(row_id, european, sentence, kept, rejected):
    tokens = [t.lower() for t in TOKEN.findall(_apply(sentence, european, row_id)["ao1990-br"])]
    assert kept in tokens and rejected not in tokens, tokens


def test_ao1990_br_takes_no_form_from_a_flat_priberam_page():
    """The VOLP lists none of these forms, and each Priberam page shows the one spelling in
    all four views. The tokens stay as written, and retor goes on the residual list as a
    change of word."""
    flat = {"angiectático", "haptotáctico", "prolepticamente", "rector", "telóptico", "tigmotactismo",
            "trofotactismo", "zigotactismo", "zigotáctico"}
    written = {fix for cell, _token, _european, fix, _rows_named, _source in _tsv("variety_fixes.tsv")
               if cell == "ao1990-br"}
    assert written & flat == set()
    keeps = {(cell, token): reason for cell, token, _european, _rows_named, reason in _tsv("variety_keeps.tsv")}
    assert keeps[("ao1990-br", "retor")].startswith("no source: a change of word")


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
