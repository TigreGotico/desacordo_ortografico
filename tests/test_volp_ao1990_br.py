"""A conversion to ao1990-br writes the form the ABL VOLP gives each word it holds.

The ABL Vocabulário Ortográfico da Língua Portuguesa (VOLP) is the official vocabulary
of Brazil. ``data/volp_ao1990_br.json`` quotes the VOLP entry of each word. Where the
VOLP lists both forms of one word, the converter writes the form with the consonant
(owner ruling: "if both forms are valid, keep the one with the consonant"). Where it
lists one form, the converter writes that form. Two entries that point to each other
with "cf." and carry different glosses are two words, so neither form becomes the
other. Where the VOLP gives the form with the consonant for one reading of a token only,
the token stays as written, because the bare form is valid for every reading. Each
expected value below comes from the VOLP entry quoted beside it.
"""
import json
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


def test_a_rejected_form_takes_the_gender_and_number_of_its_token():
    """VOLP: abstrato adj. s.m.; no abstracto. adotar v.; no adoptar. The rejected form
    with the consonant takes the token of its own row, not a token of another inflection."""
    assert convert("o abstracto e os adoptados", "ao1990-pt", "ao1990-br") == "o abstrato e os adotados"


@pytest.mark.parametrize("text", [
    # VOLP: fatura s.f. | factura s.f.; the VOLP lists faturar v. and no facturar
    "A empresa fatura milhões.",
    # VOLP: coator (ô) adj. s.m. | coactor (ô) s.m.; coactor is no adjective
    "a autoridade coatora e o ato coator",
    # VOLP: injeto s.m. | injecto s.m.; the VOLP lists injetar v. and no injectar
    "Eu injeto o remédio.",
    # VOLP: cato adj. s.m. | cacto s.m.; cato is also a form of catar v.
    "eu cato lixo",
    # VOLP: tático adj. s.m. | táctico adj.; táctico is no noun
    "o tático do time",
    # VOLP: coleta s.f. (cf. coleta (ê) s.f. "trança de cabelo") | colecta s.f.
    "a coleta do cabelo",
])
def test_a_c_p_form_for_one_reading_only_leaves_the_token(text):
    assert convert(text, "br_1971", "ao1990-br") == text


@pytest.mark.parametrize("source", ["br_1971", "ao1990"])
@pytest.mark.parametrize("text", [
    # VOLP: refletido adj. | reflectido adj.; the VOLP lists refletir v. and no reflectir,
    # so the participle has the bare form only
    ("«Os jogadores começaram a ter problemas, pois o impacto dos pés no solo era refletido "
     "para o joelho», explicou D'Ávila."),
    "o relatório foi refletido",
    # the bare form is valid for the adjective and the participle, the c/p form for the
    # adjective only, and the converter cannot see the reading
    "a superfície refletida",
])
def test_a_participle_of_a_verb_with_no_c_p_twin_stays(source, text):
    assert convert(text, source, "ao1990-br") == text


def test_a_c_p_adjective_stays_as_written():
    """VOLP: reflectido adj. The converter rejects no form the VOLP lists."""
    assert convert("um olhar reflectido", "br_1971", "ao1990-br") == "um olhar reflectido"


@pytest.mark.parametrize("source", ["br_1971", "ao1990", "ao1990-pt"])
@pytest.mark.parametrize("text", [
    # AO1990 Base XXI: a name, a firm, a brand or a title keeps its written form
    "Juntaram-se editoras como Ramal, Favela Discos, Elberec e Coletivo Farra.",
    "Quem dirigiu o filme Aventuras d'um Detetive Português?",
    "o impacto no Setor",
])
def test_a_name_inside_a_sentence_keeps_its_form(source, text):
    assert convert(text, source, "ao1990-br") == text


def test_a_name_toward_pt_pt_keeps_the_dual_step():
    """The name test belongs to the pt-BR VOLP step only."""
    assert convert("o impacto no Setor", "br_1971", "ao1990-pt") == "o impacto no Sector"


@pytest.mark.parametrize("text, expected", [
    # VOLP: setor (ô) s.m. | sector (ô) s.m.
    ("Setor público", "Sector público"),
    ("o setor", "o sector"),
    ("Fim do ano. Setor público\nSetor privado", "Fim do ano. Sector público\nSector privado"),
    # a text in capitals throughout, or with no word in lowercase, gives no case signal
    ("O COLETIVO DO SETOR", "O COLECTIVO DO SECTOR"),
    ("O Coletivo Do Setor", "O Colectivo Do Sector"),
    # a word in capitals throughout is no name
    ("o Setor é ÓTIMO", "o Setor é ÓPTIMO"),
])
def test_a_word_that_opens_a_sentence_takes_the_volp_form(text, expected):
    assert convert(text, "br_1971", "ao1990-br") == expected


@pytest.mark.parametrize("text, expected", [
    # VOLP: profilático s.m. | profiláctico adj.; the bare form is no adjective
    ("o tratamento profilático", "o tratamento profiláctico"),
    # VOLP: radioeletrônico s.m. | radioelectrônico adj.; the bare form is no adjective
    ("o circuito radioeletrônico", "o circuito radioelectrônico"),
    # VOLP: microeletrônica s.f. | microelectrônica s.f.; microeletrônico s.m. is no adjective
    ("a microeletrônica", "a microelectrônica"),
])
def test_a_bare_form_that_misses_a_reading_takes_the_c_p_form(text, expected):
    assert convert(text, "br_1971", "ao1990-br") == expected


def test_an_adjective_form_takes_the_c_p_form_of_the_adjective():
    """VOLP: elétrico adj. s.m. | eléctrico adj. The feminine elétrica is no form of the
    noun elétrico s.m., so it is the adjective, which has both forms."""
    assert convert("a energia elétrica", "br_1971", "ao1990-br") == "a energia eléctrica"


@pytest.mark.parametrize("text", [
    "um fato-macaco e dois fatos-macacos",  # VOLP: fato-macaco s.m.; pl. fatos-macaco e fatos-macacos
    "a arraia-elétrica e as arraias-elétricas",  # VOLP: arraia-elétrica s.f.; pl. arraias-elétricas
])
def test_a_compound_the_volp_lists_keeps_its_elements(text):
    assert convert(text, "br_1971", "ao1990-br") == text


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
    assert convert("Setor é ÓTIMO.", "br_1971", "ao1990-br") == "Sector é ÓPTIMO."
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


with (Path(__file__).parent.parent / "desacordo_ortografico" / "data" / "volp_ao1990_br.json").open(
        encoding="utf-8") as _f:
    ROWS = json.load(_f)


def test_every_row_quotes_its_source():
    for row in ROWS:
        assert row["source"].startswith(("VOLP: ", "Priberam ", "no source: ")), row


def test_a_two_words_row_quotes_cf_both_ways():
    """A row is two words when the VOLP points from each form to the other with "cf."."""
    for row in ROWS:
        other = row["form"] if row["form"] != row["token"] else row["european"]
        mutual = f"cf. {row['token']}" in row["source"] and f"cf. {other}" in row["source"]
        assert (row["pair"] == "two words") == mutual, row


def test_a_c_p_form_for_one_reading_only_is_marked():
    """A fix row whose quote gives the form with the consonant for one reading of the
    token only is marked "one reading" and stays out of the converter."""
    marked = {row["token"] for row in ROWS if row["pair"] == "one reading"}
    assert marked >= {
        "fatura", "faturas", "injeto", "cato", "coleta", "coator", "tático", "táticos",
        "refratário", "manufaturado", "fototático",
        "insurrecionado", "anticético", "eletromotor", "eletrocutor", "tato"}
    volp = get_lexicon().ao_br_volp
    for row in ROWS:
        if row["pair"] == "one reading":
            assert row["rows"] == "*" and row["form"] != row["token"], row
            assert row["source"].startswith("VOLP: ") and row["token"] not in volp, row


# The VOLP entries of the words that a note names as a homograph of a token, and of the
# verb of a participle that a quote names: faturar v., injetar v., retar v., injetiva s.f.,
# refletir v.; and coletar v.
VOLP_LISTED = {("verb", "faturar"), ("verb", "injetar"), ("verb", "retar"), ("noun", "injetiva"),
               ("verb", "refletir"), ("verb", "coletar")}
# Their c/p twins, which the VOLP does not list (coletar has the twin colectar v.)
VOLP_ABSENT = {"facturar", "injectar", "rectar", "injectiva", "reflectir"}
_CLASSES = {"adj": "adjective", "s.m": "noun", "s.f": "noun", "s.2g": "noun", "v": "verb"}


def _classes(entry):
    """The word classes of one VOLP entry ("coator (ô) adj. s.m.": adjective, noun)."""
    entry = re.sub(r'\([^()]*\)|"[^"]*"', " ", re.sub(r"\([^()]*\([^()]*\)[^()]*\)", " ", entry))
    return {_CLASSES[t] for t in re.findall(r"(?<![\w.])(adj|s\.[mf]|s\.2g|v)\.", entry.split(";")[0])}


def _twin(word, token, form):
    """``word`` with the c or p that ``form`` adds to ``token`` (faturar -> facturar)."""
    i = next(i for i in range(len(form)) if form[:i] + form[i + 1:] == token)
    return word[:i] + form[i] + word[i:]


def _valid_for_every_reading(row):
    """True when the bare entry of a VOLP dual row covers every word class of its c/p
    entry, and either covers a class the c/p entry lacks or a note names a VOLP homograph
    of the token with no c/p twin. A past participle of a VOLP verb with no c/p twin is a
    verb reading of the bare form: "refletido adj. | reflectido adj.; VOLP: refletir v.;
    no reflectir"."""
    body = row["source"].removeprefix("VOLP: ")
    only = re.match(r"([^;|]*); (\S+) ([^;]*?) is an? \w+ only", body)
    if only:  # "profiláctico adj.; profilático s.m. is a noun only"
        cons_entry, head, bare_entry = only.groups()
    elif "|" in body:
        bare_entry, cons_entry = (side.strip() for side in body.split("|", 1))
        head = bare_entry.split()[0]
    else:
        return False
    bare, cons = _classes(bare_entry), _classes(cons_entry)
    if row["token"] not in (head, head + "s"):
        bare, cons = bare - {"noun"}, cons - {"noun"}
    verb = re.search(r"VOLP: (\S+)(ar|er|ir) v\.; no (\S+)$", body)
    if (verb and re.fullmatch(rf"{verb[1]}{verb[2][0]}d[oa]s?", row["token"])
            and ("verb", verb[1] + verb[2]) in VOLP_LISTED
            and verb[3] == _twin(verb[1] + verb[2], row["token"], row["form"]) in VOLP_ABSENT):
        bare |= {"verb"}
    note = re.search(r"\b(?:never|not) the (verb|noun|adjective) (\S+)", body)
    homograph = (note and (note[1], note[2]) in VOLP_LISTED
                 and _twin(note[2], row["token"], row["form"]) in VOLP_ABSENT) or f"cf. {head} (" in body
    return cons <= bare and bool(bare - cons or homograph)


def test_a_one_reading_row_keeps_a_bare_form_valid_for_every_reading():
    """The bare form of a "one reading" row is valid for every reading of its token."""
    wrong = [row["token"] for row in ROWS if row["pair"] == "one reading" and not _valid_for_every_reading(row)]
    assert wrong == [], wrong


def test_a_row_whose_bare_form_is_valid_for_every_reading_is_marked():
    unmarked = [row["token"] for row in ROWS if row["rows"] == "*" and row["pair"] == "one word"
                and row["form"] != row["token"] and row["source"].startswith("VOLP: ")
                and _valid_for_every_reading(row)]
    assert unmarked == [], unmarked


def test_a_homograph_with_a_c_p_twin_marks_no_row():
    """VOLP: coletar v. | colectar v. A note that names coletar gives the token coleta no
    reading that colecta lacks."""
    row = {"token": "coleta", "form": "colecta", "rows": "*", "pair": "one reading",
           "source": "VOLP: coleta s.f. | colecta s.f.; never the verb coletar"}
    assert not _valid_for_every_reading(row)


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
    assert wrong == [], wrong


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
