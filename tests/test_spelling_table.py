"""The spelling table ``data/spelling.json`` is the only source of the 1911 pairs, the
pre-1911 archaisms and the AO1990 word maps that convert() and detect() read.

Each expected conversion below comes from a row of the table, as the tugalex lists gave
it: pharmacia -> farmácia (a curated 1911 pair), comsigo -> consigo and architecto ->
arquitecto (tugalex ``archaisms.csv``), acção -> ação (``acordo_ortografico_pt_PT.csv``)
and idéia -> ideia (``acordo_ortografico_pt_BR.csv``).
"""
import json
from pathlib import Path

import pytest
import tugalex

import desacordo_ortografico
from desacordo_ortografico import OrthographyConverter, detect
from desacordo_ortografico import lexicon as lexicon_module
from desacordo_ortografico.eras import EDGES
from desacordo_ortografico.lexicon import Lexicon, get_lexicon

_TABLE = Path(desacordo_ortografico.__file__).parent / "data" / "spelling.json"


def _table():
    with open(_TABLE, encoding="utf-8") as f:
        return json.load(f)


def _rows():
    return _table()["rows"]


_SPELLING_LISTS = {"archaic_words", "archaic_words_br", "ao_pt", "ao_br",
                   "archaisms_path", "ao_pt_path", "ao_br_path"}


class _WordListOnly(tugalex.TugaLexicon):
    """A TugaLexicon whose spelling lists raise once it is built; the word list works."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.built = True

    def __getattribute__(self, name):
        if name in _SPELLING_LISTS and object.__getattribute__(self, "__dict__").get("built"):
            raise AssertionError(f"desacordo read TugaLexicon.{name}")
        return super().__getattribute__(name)


@pytest.fixture
def table_only_lexicon(monkeypatch):
    load = lexicon_module._load

    def load_without_1911_json(name):
        if name == "reform_1911_irregular.json":
            raise AssertionError("desacordo read reform_1911_irregular.json")
        return load(name)

    monkeypatch.setattr(tugalex, "TugaLexicon", _WordListOnly)
    monkeypatch.setattr(lexicon_module, "_load", load_without_1911_json)
    lex = Lexicon()
    assert isinstance(lex.tuga, _WordListOnly)
    return lex


@pytest.mark.parametrize("text,source,target,expected", [
    ("a pharmacia", "etymological", "reforma_1911", "a farmácia"),
    ("a farmácia", "reforma_1911", "etymological", "a pharmacia"),
    ("comsigo", "etymological", "ao1990-pt", "consigo"),
    ("architecto", "etymological", "reforma_1911", "arquitecto"),
    ("a acção", "pt_1973", "ao1990-pt", "a ação"),
    ("a ação", "ao1990-pt", "pt_1973", "a acção"),
    ("a idéia", "br_1971", "ao1990-br", "a ideia"),
    ("o sector", "ao1990-br", "ao1990-pt", "o sector"),
])
def test_convert_reads_no_tugalex_spelling_list(table_only_lexicon, text, source, target, expected):
    assert OrthographyConverter(table_only_lexicon).convert(text, source, target).text == expected


@pytest.mark.parametrize("text,label,marker", [
    ("A pharmacia fica longe.", "etymological", "etym:pharmacia"),
    ("Falei d'ella hontem.", "etymological", "etym-pattern:d'ella"),
    ("A acção foi rápida.", "pt_1973", "pre-ao90-pt:acção"),
    ("A idéia foi boa.", "br_1971", "pre-ao90-br:idéia"),
])
def test_detect_reads_no_tugalex_spelling_list(table_only_lexicon, text, label, marker):
    result = detect(text, lexicon=table_only_lexicon)
    assert result.id == label
    assert marker in result.markers


def test_every_row_names_its_edge_and_its_source():
    rows = _rows()
    edges = {(a, b) for a, b, _name in EDGES}
    # a pre-1911 form whose 1911 form no source decides gives its AO1990 forms only
    edges |= {("etymological", "ao1990-pt"), ("etymological", "ao1990-br")}
    assert [r for r in rows if (r["era"], r["target"]) not in edges] == []
    assert [r for r in rows if not r["source"] or not isinstance(r["curated"], bool)] == []
    keys = [(r["form"], r["era"], r["target"]) for r in rows]
    assert len(keys) == len(set(keys))


def _cites(source, entry):
    """True when ``source`` is ``entry``, alone or followed by a note in parentheses."""
    return source == entry or (source.startswith(f"{entry} (") and source.endswith(")"))


def test_every_row_cites_an_entry_of_the_sources():
    table = _table()
    sources, groups = table["_sources"], table["_groups"]
    assert [r for r in table["rows"] if not any(_cites(r["source"], s) for s in sources)] == []
    # a curated pre-1911 pair names its group; a curated row out of 1911 quotes its clause
    curated = [r for r in table["rows"] if r["curated"] and r["era"] == "etymological"]
    assert curated
    assert [r for r in curated if r["source"] not in {f"{sources[0]} ({g})" for g in groups}] == []


def test_no_row_has_an_empty_value():
    # convert() reads an empty 1911 value as a table hit and the rules then raise, and an
    # empty AO1990 value deletes the word; a form with no single value needs its own rule
    assert [r for r in _rows() if "" in r["value"].split("|")] == []


# A pt-BR AO1990 cell gives desacordo's form: the form with the consonant of a dual cell,
# else its only form. These br_1971 rows give a form whose ABL VOLP form
# (Lexicon.ao_br_volp, from data/volp_ao1990_br.json) is another form. For the first five
# the VOLP does not list the form of the cell ("VOLP: intersectar v.; no intersetar").
# For the next three it lists both forms ("VOLP:
# bissetor (ô) adj. s.m. | bissector (ô) adj. s.m."), and the cell gives only the bare one.
# For the last two it writes the hyphen that the cell drops ("VOLP: contra-erva s.f.; pl.
# contra-ervas"). convert() writes the VOLP form for each of them, because it applies the
# VOLP last.
VOLP_CONTRADICTIONS = {
    ("intersectar", "intersetar", "intersectar"),
    ("perfeccional", "perfecional", "perfeccional"),
    ("perfeccionismo", "perfecionismo", "perfeccionismo"),
    ("perfeccionista", "perfecionista", "perfeccionista"),
    ("perfeccionístico", "perfecionístico", "perfeccionístico"),
    ("bissector", "bissetor", "bissector"),
    ("fotelectricidade", "foteletricidade", "fotelectricidade"),
    ("idielectricidade", "idieletricidade", "idielectricidade"),
    ("contra-erva", "contraerva", "contra-erva"),
    ("macro-jê", "macrojê", "macro-jê"),
}


def _cell_form(value):
    return max(value.split("|"), key=len)


def test_br_1971_rows_against_the_volp_decisions():
    volp = get_lexicon().ao_br_volp
    found = set()
    for r in _rows():
        form = _cell_form(r["value"])
        if r["era"] == "br_1971" and volp.get(form, form) != form:
            found.add((r["form"], r["value"], volp[form]))
    assert found == VOLP_CONTRADICTIONS


@pytest.mark.parametrize("form,_value,volp_form", sorted(VOLP_CONTRADICTIONS))
def test_convert_writes_the_volp_form_of_a_contradicting_row(form, _value, volp_form):
    assert desacordo_ortografico.convert(form, "br_1971", "ao1990-br") == volp_form
