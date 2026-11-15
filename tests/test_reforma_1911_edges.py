"""Text in the 1911 spelling converts to the norms that follow it.

Each sentence comes from Eça de Queirós, Contos (Porto, Chardron, 1913), printed in the
spelling of the Formulário Ortográfico of 1911 (Project Gutenberg #31347). Each expected
form comes from the clause on its row: the Acordo Ortográfico of 1945 for pt_1945 and the
Formulário Ortográfico of 1943 for br_1943. rules.py quotes the clauses in full.
"""
import json
import time
from pathlib import Path

import pytest

import desacordo_ortografico
from desacordo_ortografico import convert, rules

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
])
def test_1911_print_reaches_ao1990(text, target, expected):
    assert convert(text, "reforma_1911", target) == expected


_SINGULAR_LIMIT = (
    "1911 Base XIV writes the singular contêm (\"contêm, do verbo conter\"); from 1945 on the "
    "same letters spell the plural, and text between the Portuguese and Brazilian norms passes "
    "through 1911 with that plural, so the compounds of ter and vir stay as written")


@pytest.mark.xfail(strict=True, reason=_SINGULAR_LIMIT)
@pytest.mark.parametrize("text,target,expected", [
    # the subject is singular: 1945 Base XIII "convém, mantém"; AO1990 keeps the acute
    ("--Senhor, convêm que me deixeis no Cêrro!", "pt_1945", "--Senhor, convém que me deixeis no Cêrro!"),
    ("--Senhor, convêm que me deixeis no Cêrro!", "ao1990-pt", "--Senhor, convém que me deixeis no Cerro!"),
])
def test_1911_singular_of_a_ter_or_vir_compound(text, target, expected):
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
    # a regular form of a known verb (viver, ser, opor, perdoar) and a contraction of de
    ("vivêra", "vivera"), ("fôram", "foram"), ("opôrem", "oporem"), ("perdôa", "perdoa"),
    ("dêsses", "desses"),
])
def test_1945_drops_the_differential_circumflex(old, new):
    assert convert(old, "reforma_1911", "pt_1945") == new


@pytest.mark.parametrize("word", ["lêem", "vêem", "crêem", "dêem", "pôde", "pêlo"])
def test_1945_keeps_the_circumflex_whatever_the_word_set(word):
    # Base XXI keeps the hiatus ee and Base XXII keeps pôde and pêlo, even when the bare
    # letters spell a word
    assert rules.drop_differential_1945(word, lambda w: True) == word


@pytest.mark.parametrize("old,new", [
    ("Alêm-rio", "Além-rio"), ("ninguêm", "ninguém"), ("Jerusalêm", "Jerusalém"),
    ("armazêns", "armazéns"), ("alguêm", "alguém"), ("TAMBÊM", "TAMBÉM"),
    # a noun, not a compound of ter: 1945 Base XIII and 1943, 7.ª write vintém
    ("vintêm", "vintém"),
])
def test_oxytone_em_takes_the_acute(old, new):
    for target in ("pt_1945", "br_1943"):
        assert convert(old, "reforma_1911", target) == new


@pytest.mark.parametrize("word", [
    # 1911 Base XI names the words that keep the initial sc; these foreign words are none
    # of them
    "Science", "Scion", "scene",
    # 1911 Base XXVIII marks one of two Portuguese homographs: a foreign word whose bare
    # letters spell no Portuguese word carries no 1911 differential circumflex
    "prêtres", "prête", "être", "même", "rêve", "bête", "vôtre", "êtes",
    # 1945 Base XIII "tão (não tam)" is the adverb; Eça's tam-tam is a gong
    "tam-tam",
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


@pytest.mark.parametrize("text,source", [
    ("Peuple de prêtres, peuple de rois", "br_1943"),
    ("Il faut être bête.", "reforma_1911"),
    # Eça de Queirós, in the spelling before 1911
    ("um tam-tam argentino e melancólico ressoava", "etymological"),
])
def test_foreign_words_and_the_gong_stay(text, source):
    for target in ("pt_1945", "pt_1973", "ao1990-pt"):
        assert convert(text, source, target) == text


@pytest.mark.parametrize("text", [
    "Quiz vêl-a e pôz-se a correr para a aldêa de Corrêa, ao Musêo.", "a campêa"])
def test_pre_1911_shapes_keep_the_circumflex(text):
    # the etymological edge leaves these pre-1911 shapes (1945: vê-la, pôs-se, aldeia,
    # Correia, Museu, campeia); dropping the circumflex would not give the 1945 form
    assert convert(text, "etymological", "pt_1945") == text


@pytest.mark.xfail(strict=True, reason=(
    "cote is a Portuguese word, so the letters of Côte cannot tell the French word from a "
    "1911 differential"))
def test_cote_d_azur_stays():
    assert convert("Passou férias na Côte d'Azur.", "br_1943", "pt_1945") == "Passou férias na Côte d'Azur."


@pytest.mark.xfail(strict=True, reason=(
    "the initial sc rule reads the word families of 1911 Base XI, and some English words "
    "share their letters"))
def test_english_sc_words_stay():
    text = "the scientific method and a sceptical scenario"
    assert convert(text, "reforma_1911", "pt_1945") == text


@pytest.mark.parametrize("target", ["pt_1945", "pt_1973"])
def test_scetro_keeps_the_p_in_portugal(target):
    # 1945 Base VI, 2.°: "ceptro [...] (p interior geralmente proferido no Brasil, mas
    # predominantemente mudo em Portugal)"
    assert convert("O scetro", "reforma_1911", target) == "O ceptro"


@pytest.mark.xfail(strict=True, reason=(
    "data/base_iv.json maps cetro to ceptro on the Brazilian edges; the Bases of 1931, § 1.º "
    "1.º, write cetro"))
def test_scetro_loses_the_s_in_brazil():
    # Bases of 1931, § 1.º: "Eliminar: 1.º As consoantes mudas: cetro, fruto, sinal em vez
    # de sceptro, fructo, signal"
    assert convert("O scetro", "reforma_1911", "br_1943") == "O cetro"


@pytest.mark.parametrize("token", [
    "a" * 3000 + "êm", "ba" * 1500 + "êm", "ê" * 3000, "b" * 3000 + "ôr", "êb" * 1500 + "a"])
def test_a_long_token_converts_in_linear_time(token):
    start = time.perf_counter()
    for source, target in (("reforma_1911", "pt_1945"), ("pt_1973", "br_1943")):
        convert(token, source, target)
    assert time.perf_counter() - start < 2.0


def _rows_out_of_1911():
    with open(_TABLE, encoding="utf-8") as f:
        return [r for r in json.load(f)["rows"] if r["era"] == "reforma_1911"]


def test_every_row_out_of_1911_quotes_its_clause():
    rows = _rows_out_of_1911()
    assert {(r["form"], r["target"]) for r in rows} == {
        (form, target) for form in ("quási", "tam", "quam", "teem", "veem")
        for target in ("pt_1945", "br_1943")} | {("scetro", "pt_1945")}
    for r in rows:
        assert r["source"].startswith(("Acordo Ortográfico de 1945", "Formulário Ortográfico de 1943"))
        assert '"' in r["source"] and r["value"] in r["source"]


@pytest.mark.parametrize("row", _rows_out_of_1911(), ids=lambda r: f"{r['form']}-{r['target']}")
def test_convert_reads_each_row_out_of_1911(row):
    assert convert(row["form"], "reforma_1911", row["target"]) == row["value"]
