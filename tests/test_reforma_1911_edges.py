"""Text in the 1911 spelling converts to the norms that follow it.

Each sentence comes from Eça de Queirós, Contos (Porto, Chardron, 1913), printed in the
spelling of the Formulário Ortográfico of 1911 (Project Gutenberg #31347). Each expected
form comes from the clause on its row: the Acordo Ortográfico of 1945 for pt_1945 and the
Formulário Ortográfico of 1943 for br_1943. rules.py quotes the clauses in full.
"""
import json
from pathlib import Path

import pytest

import desacordo_ortografico
from desacordo_ortografico import convert

_TABLE = Path(desacordo_ortografico.__file__).parent / "data" / "spelling.json"


@pytest.mark.parametrize("text,target,expected", [
    # 1945 Base XIII "também"; 1943, 7.ª "também"
    ("E tambêm quanta imprudência!", "pt_1945", "E também quanta imprudência!"),
    ("E tambêm quanta imprudência!", "br_1943", "E também quanta imprudência!"),
    # 1945 Base XIII "armazém"; 1943, 7.ª "armazém"
    ("No seu armazêm!", "pt_1945", "No seu armazém!"),
    ("No seu armazêm!", "br_1943", "No seu armazém!"),
    # 1945 Base IX "quase (em vez de quási)"; 1943, 33. "quase"
    ("Vi-o chorar, àquele vélho de quási sessenta anos.", "pt_1945",
     "Vi-o chorar, àquele vélho de quase sessenta anos."),
    ("Vi-o chorar, àquele vélho de quási sessenta anos.", "br_1943",
     "Vi-o chorar, àquele vélho de quase sessenta anos."),
    # 1945 Base XXVII "tranquilo"; 1943, 12.ª "tranqüilo", "eloqüente"
    ("No entanto estava tranqùilo.", "pt_1945", "No entanto estava tranquilo."),
    ("No entanto estava tranqùilo.", "br_1943", "No entanto estava tranqüilo."),
    ("Era o Mensageiro dos Deuses, o leve, eloqùente Mercúrio.", "br_1943",
     "Era o Mensageiro dos Deuses, o leve, eloqüente Mercúrio."),
    # 1931 Bases § 1.º 4.º "ciência"; 1943, 19. "ciência", "cintilar"
    ("De-certo, a sua sciência hereditária", "pt_1945", "De-certo, a sua ciência hereditária"),
    ("Cada uma das suas penitências scintilava", "br_1943", "Cada uma das suas penitências cintilava"),
    # 1945 Base XIII "tão (não tam)"; 1943, 28. Observação 2.ª "tão"
    ("É tam triste, que a condenso.", "pt_1945", "É tão triste, que a condenso."),
    ("É tam triste, que a condenso.", "br_1943", "É tão triste, que a condenso."),
    # 1945 Base XX "têm"; 1943, 7.ª Observação 2.ª "(êles) têm"
    ("--A mim teem-me afirmado", "pt_1945", "--A mim têm-me afirmado"),
    ("vocês teem os seus...", "br_1943", "vocês têm os seus..."),
    # 1945 Base XXII "ele (ê), pronome"; 1943, 14.ª keeps "êle"
    ("--De onde é êle?", "pt_1945", "--De onde é ele?"),
    ("--De onde é êle?", "br_1943", "--De onde é êle?"),
    # 1945 Base XXII drops the accent of este and keeps pêlo; 1943, 14.ª keeps "êste",
    # "sôbre"
    ("E dêste modo Jacinto ficava diante do espelho, passando pêlos sôbre o seu pêlo",
     "pt_1945", "E deste modo Jacinto ficava diante do espelho, passando pêlos sobre o seu pêlo"),
    ("E dêste modo Jacinto ficava diante do espelho, passando pêlos sôbre o seu pêlo",
     "br_1943", "E dêste modo Jacinto ficava diante do espelho, passando pêlos sôbre o seu pêlo"),
    # 1945 Base XXI "voos"; 1943, 10.ª "vôos"
    ("Ai! as aladas fantasias batem o vôo", "pt_1945", "Ai! as aladas fantasias batem o voo"),
    ("Ai! as aladas fantasias batem o vôo", "br_1943", "Ai! as aladas fantasias batem o vôo"),
])
def test_1911_print_converts(text, target, expected):
    assert convert(text, "reforma_1911", target) == expected


@pytest.mark.parametrize("text,target,expected", [
    ("E tambêm quanta imprudência!", "ao1990-pt", "E também quanta imprudência!"),
    ("E tambêm quanta imprudência!", "ao1990-br", "E também quanta imprudência!"),
    ("Vi-o chorar, àquele vélho de quási sessenta anos.", "ao1990-br",
     "Vi-o chorar, àquele vélho de quase sessenta anos."),
    ("De-certo, a sua sciência hereditária", "ao1990-pt", "De-certo, a sua ciência hereditária"),
    ("É tam triste, que a condenso.", "ao1990-br", "É tão triste, que a condenso."),
    ("--A mim teem-me afirmado", "ao1990-pt", "--A mim têm-me afirmado"),
    # AO1990 Base IX 5º c): "As formas verbais têm e vêm, 3.ªs pessoas do plural do
    # presente do indicativo de ter e vir"
    ("vocês teem os seus...", "ao1990-br", "vocês têm os seus..."),
    ("--De onde é êle?", "ao1990-pt", "--De onde é ele?"),
    ("--Senhor, convêm que me deixeis no Cêrro!", "ao1990-pt", "--Senhor, convêm que me deixeis no Cerro!"),
])
def test_1911_print_reaches_ao1990(text, target, expected):
    assert convert(text, "reforma_1911", target) == expected


@pytest.mark.parametrize("word", [
    # 1945 Base XXII keeps these forms
    "pêlo", "pêlos", "pêra", "pôlo", "pôr", "pôde", "dêmos", "côa",
    # 1945 Base XXI keeps the hiatus ee; Base XX the plural têm
    "lêem", "vêem", "crêem", "dêem", "têm", "vêm",
    # an accent that the position of the stress needs: an oxytone, a proparoxytone, a
    # paroxytone in -l or -ão, and an enclitic form
    "três", "você", "pôs", "pêssego", "sêmola", "silêncio", "cônsul", "bênção", "corrê-la",
])
def test_1945_keeps_the_circumflex(word):
    assert convert(word, "reforma_1911", "pt_1945") == word


@pytest.mark.parametrize("old,new", [
    # 1945 Base XXII: "côr (ô), substantivo"; "fez (ê)"; "portuguesa (ê)"; "vezes (ê)"
    ("côr", "cor"), ("fêz", "fez"), ("portuguêsa", "portuguesa"), ("vêzes", "vezes"),
    ("compôr", "compor"), ("Êste", "Este"), ("sobr'ôlho", "sobr'olho"), ("sal-gêma", "sal-gema"),
    # 1945 Base XXI: "enjoo"
    ("enjôo", "enjoo"),
])
def test_1945_drops_the_differential_circumflex(old, new):
    assert convert(old, "reforma_1911", "pt_1945") == new


@pytest.mark.parametrize("old,new", [
    ("Alêm-rio", "Além-rio"), ("ninguêm", "ninguém"), ("Jerusalêm", "Jerusalém"),
    ("armazêns", "armazéns"), ("alguêm", "alguém"), ("TAMBÊM", "TAMBÉM"),
])
def test_oxytone_em_takes_the_acute(old, new):
    for target in ("pt_1945", "br_1943"):
        assert convert(old, "reforma_1911", target) == new


@pytest.mark.parametrize("word", [
    # from 1945 on, the compounds of ter and vir in -têm and -vêm are the plural
    # (conclusão 20 of 1945; 1943, 7.ª Observação 2.ª "(êles) contêm, (elas) convêm")
    "contêm", "convêm", "mantêm", "provêm",
    # 1911 Base XI names the words that keep the initial sc; a foreign word is none of them
    "Science", "Scion", "scene",
])
def test_out_of_1911_leaves_the_word(word):
    for target in ("pt_1945", "br_1943"):
        assert convert(word, "reforma_1911", target) == word


@pytest.mark.parametrize("text", [
    "A atividade do vulcão diminuiu, mas os geólogos mantêm a vigilância apertada.",
    "O estudo foi realizado por zoólogos do Swansea University's College of Science.",
])
def test_text_between_the_norms_keeps_the_plural_and_the_foreign_word(text):
    assert convert(text, "pt_1973", "br_1943") == text


def _rows_out_of_1911():
    with open(_TABLE, encoding="utf-8") as f:
        return [r for r in json.load(f)["rows"] if r["era"] == "reforma_1911"]


def test_every_row_out_of_1911_quotes_its_clause():
    rows = _rows_out_of_1911()
    assert {(r["form"], r["target"]) for r in rows} == {
        (form, target) for form in ("quási", "tam", "quam", "teem", "veem")
        for target in ("pt_1945", "br_1943")}
    for r in rows:
        assert r["source"].startswith(("Acordo Ortográfico de 1945", "Formulário Ortográfico de 1943"))
        assert '"' in r["source"] and r["value"] in r["source"]


@pytest.mark.parametrize("row", _rows_out_of_1911(), ids=lambda r: f"{r['form']}-{r['target']}")
def test_convert_reads_each_row_out_of_1911(row):
    assert convert(row["form"], "reforma_1911", row["target"]) == row["value"]
