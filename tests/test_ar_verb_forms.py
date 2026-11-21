"""The regular forms of an -ar verb convert like its infinitive.

Cunha & Cintra, *Nova Gramática do Português Contemporâneo*, 7.ª ed., Lexikon 2017, cap. 13
"Verbo": "todos os verbos regulares da 1.ª conjugação formam os seus tempos pelo modelo de
cantar" (p. 419). So an infinitive that a table converts (adoptar -> adotar, Base IV 1º b:
"adoção, adotar") has its present, preterite, imperfect, pluperfect, future, conditional,
subjunctive, imperative, gerund and participle converted by the same rule: the stem stays and
the ending is the same on both sides.

The VOP (Vocabulário Ortográfico do Português, Portal da Língua Portuguesa) tags lemma 54366
"decepcionar" as Brasil, "variante AO de : dececionar ( Portugal)", and lemma 191820
"dececionar" as Portugal, conjugated "dececionou". The VOLP holds "decepcionar v.; no
dececionar" for Brazil, so a pt-BR target keeps the c of every form.
"""
import pytest

from desacordo_ortografico import convert, rules
from desacordo_ortografico.lexicon import get_lexicon

PT = "ao1990-pt"
BR = "ao1990-br"
PT_GROUP = frozenset({"1911-word-map", "trema", "ao-map-consonant", "base-iv",
                      "initial-sc", "ao-map-diacritic"})


@pytest.mark.parametrize("old, new", [
    ("decepcionou", "dececionou"),
    ("decepcionaram", "dececionaram"),
    ("decepciona", "dececiona"),
    ("adoptou", "adotou"),
    ("actuou", "atuou"),
    ("projectou", "projetou"),
    ("projectaram", "projetaram"),
    ("detecta", "deteta"),
    ("Decepcionou os economistas.", "Dececionou os economistas."),
    ("DECEPCIONOU", "DECECIONOU"),
])
def test_pt_1973_forms_reach_ao1990_pt(old, new):
    assert convert(old, "pt_1973", PT) == new


# The endings of the model verb cantar (cap. 13, pp. 402-408), on the stems adopt- and adot-.
@pytest.mark.parametrize("ending", [
    "o", "as", "a", "amos", "ais", "am",
    "ei", "aste", "ou", "astes", "aram",
    "ava", "avas", "ávamos", "áveis", "avam",
    "ara", "aras", "áramos", "áreis",
    "arei", "arás", "ará", "aremos", "areis", "arão",
    "aria", "arias", "aríamos", "aríeis", "ariam",
    "e", "es", "emos", "eis", "em",
    "asse", "asses", "ássemos", "ásseis", "assem",
    "ares", "armos", "ardes", "arem",
    "ai", "ando", "ado", "ada", "ados", "adas",
])
def test_every_ending_of_the_model_verb(ending):
    assert convert("adopt" + ending, "pt_1973", PT) == "adot" + ending


@pytest.mark.parametrize("old, new", [
    # ficar - fiquei (cap. 13, p. 428): both rows end in -c, so both take -qu before e
    ("electrifiquei", "eletrifiquei"),
    ("electrifique", "eletrifique"),
    ("rectifiquem", "retifiquem"),
    ("rectificou", "retificou"),
])
def test_a_stem_in_c_changes_before_e_on_both_sides(old, new):
    assert convert(old, "pt_1973", PT) == new


@pytest.mark.parametrize("old, new", [
    ("dececionou", "decepcionou"),
    ("dececionaram", "decepcionaram"),
    ("adotou", "adoptou"),
    ("projetaram", "projectaram"),
    ("deteta", "detecta"),
])
def test_ao1990_pt_forms_read_back_to_pt_1973(old, new):
    assert convert(old, PT, "pt_1973") == new


@pytest.mark.parametrize("src, text, out", [
    ("pt_1973", "O ténue crescimento decepcionou os economistas.", "O tênue crescimento decepcionou os economistas."),
    ("br_1971", "O tênue crescimento decepcionou os economistas.", "O tênue crescimento decepcionou os economistas."),
    ("pt_1973", "Eles decepcionaram o mercado.", "Eles decepcionaram o mercado."),
    ("pt_1973", "O sensor detectou o sinal.", "O sensor detectou o sinal."),
])
def test_a_pt_br_target_keeps_the_c(src, text, out):
    """The VOLP rejects dececionar and lists detetar | detectar, so pt-BR keeps the c."""
    assert convert(text, src, BR) == out


@pytest.mark.parametrize("word, pt", [("conjecturou", "conjeturou"), ("coactou", "coatou")])
def test_a_pt_br_target_keeps_the_consonant_of_a_dual_verb(word, pt):
    """The VOLP lists conjeturar | conjecturar and coatar | coactar, so pt-BR keeps the
    consonant of every form; pt-PT drops it."""
    assert convert(word, "pt_1973", PT) == pt
    assert convert(word, "pt_1973", BR) == word


def test_a_pt_br_target_drops_the_p_where_the_vocabulary_does():
    assert convert("adoptou", "pt_1973", BR) == "adotou"
    assert convert("projectaram", "pt_1973", BR) == "projetaram"


@pytest.mark.parametrize("src", ["pt_1973", "br_1971"])
def test_a_dual_verb_keeps_the_consonant_in_every_form(src):
    """datilografar | dactilografar is a Base IV 1º c dual: the infinitive writes the form with
    the consonant (VOLP: "datilografar v. | dactilografar v."), and so does each form."""
    assert convert("datilografar", src, PT) == "dactilografar"
    assert convert("datilografou", src, PT) == "dactilografou"
    assert convert("dactilografou", src, PT) == "dactilografou"
    assert convert("dactilografou", src, BR) == "dactilografou"


def test_a_row_that_a_feature_switches_off_gives_no_verb_form():
    assert convert("decepcionou", "pt_1973", PT, features={"ao-map-diacritic"}) == "decepcionou"
    assert convert("decepcionou", "pt_1973", PT, features=PT_GROUP) == "dececionou"


def test_the_tugaphone_spelling_step_converts_the_forms():
    assert convert("decepcionou os economistas", "etymological", PT, features=PT_GROUP) \
        == "dececionou os economistas"


def test_a_modern_word_of_its_own_stays():
    """retracto is on the modern word list; the verb form of retractar -> retratar leaves it,
    and the same row still converts the other forms."""
    lex = get_lexicon()
    assert "retracto" in lex.wordset and "retractar" in lex.ao_pt_old2new
    for target in (PT, BR):
        assert convert("retracto", "pt_1973", target) == "retracto"
    assert convert("retractou", "pt_1973", PT) == "retratou"


@pytest.mark.parametrize("word", ["sobreexcedeu", "reflectiu"])
def test_an_er_or_ir_verb_form_stays_as_written(word):
    """Only -ar verbs derive forms. sobreexceder -> sobre-exceder and reflectir -> refletir are
    rows of the map, and no rule derives their forms."""
    lex = get_lexicon()
    assert "sobreexceder" in lex.ao_pt_old2new and "reflectir" in lex.ao_pt_old2new
    assert convert(word, "pt_1973", PT) == word


@pytest.mark.parametrize("src", ["ao1990-pt", "pt_1973", "br_1971"])
@pytest.mark.parametrize("text", [
    "Os coletes amarelos saíram à rua.",
    "A coleta-chave do projeto.",
])
def test_a_noun_listed_in_its_plural_stays_toward_pt_br(src, text):
    """coletes is the plural of colete (Priberam: "Peça de vestuário, sem mangas, que se veste
    geralmente por cima da camisa"), a word of the list; the VOLP row coletar -> colectar gives
    it no verb form, whole or as an element of a compound."""
    assert convert(text, src, BR) == text


@pytest.mark.parametrize("text", ["Puseram-lhe um colete-de-forças.", "o acupunturo-chave", "o coato-chave"])
def test_an_element_of_a_compound_that_is_listed_stays_toward_pt_br(text):
    assert convert(text, PT, BR) == text


@pytest.mark.parametrize("text", [
    "Ele vestiu o colete e saiu.",
    "O retrato da avó está na sala.",
    "O pintor retratou a cidade.",
    "O filme retrata a época.",
    "Os coletes e os retratos.",
])
def test_a_noun_or_the_verb_of_a_noun_does_not_gain_the_consonant_going_back(text):
    """retrato never gains the consonant (Priberam: "Imagem de pessoa reproduzida pela pintura,
    pelo desenho ou pela fotografia"), and no form of retratar or coletar does either."""
    assert convert(text, PT, "pt_1973") == text


def test_other_verb_forms_still_gain_the_consonant_going_back():
    assert convert("Ele projeta e batiza.", PT, "pt_1973") == "Ele projecta e baptiza."


@pytest.mark.parametrize("word, pt", [
    ("decepcionada", "dececionada"), ("decepcionadas", "dececionadas"),
    ("adoptados", "adotados"), ("projectada", "projetada"),
])
def test_a_feminine_or_plural_participle_of_a_row_verb_converts(word, pt):
    """decepcionado is a listed word, and its feminine and plural come from the row of
    decepcionar, not from a noun of their own."""
    assert convert(word, "pt_1973", PT) == pt


def test_a_held_dual_adjective_plural_keeps_its_consonant_toward_pt_br():
    """The VOLP keeps insurreccionar with its c, so insurreccionáveis does too."""
    assert convert("insurreccionáveis", "pt_1973", BR) == "insurreccionáveis"


class TestLookupWithArForms:
    TABLE = {"adoptar": "adotar", "electrificar": "eletrificar", "ficar": "fiçar",
             "pedra-de-afiar": "pedra de afiar", "agir": "agir"}

    @pytest.mark.parametrize("word, form", [
        ("adoptar", "adotar"),
        ("adoptaram", "adotaram"),
        ("adoptávamos", "adotávamos"),
        ("electrifiquei", "eletrifiquei"),
    ])
    def test_forms(self, word, form):
        assert rules.lookup_with_ar_forms(word, self.TABLE) == form

    @pytest.mark.parametrize("word", [
        "adoptor",         # no -ar ending of the model verb
        "adopter",         # the -er ending is not derived
        "fiquei",          # the two sides of the row end in different letters
        "pedra-de-afiara",  # the new form is a locution
        "agiu",            # -ir
        "xyz",
    ])
    def test_no_form(self, word):
        assert rules.lookup_with_ar_forms(word, self.TABLE) is None

    @pytest.mark.parametrize("word", ["colete", "coleto", "coletes"])
    def test_a_verb_of_a_noun_gives_no_form(self, word):
        table = {"coletar": "colectar"}
        assert rules.lookup_with_ar_forms(word, table) is None
        assert rules.lookup_with_ar_forms("coletar", table) == "colectar"

    def test_a_word_of_the_modern_list_gives_no_form(self):
        assert rules.lookup_with_ar_forms("adoptou", self.TABLE, {"adoptou"}) is None
        assert rules.lookup_with_ar_forms("adoptar", self.TABLE, {"adoptar"}) == "adotar"
