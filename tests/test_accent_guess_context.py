"""The 1911 accent guess reads the part-of-speech tags and the determiner before a word.

A bare form that only a verb inflection makes a word takes its accent when the caller
tags it NOUN or ADJ: "a historia" is "a história", "ele pratica" stays (Dicionário
Priberam, conjugation of falar: ele fala). A bare form that only a plural makes a word
takes its accented singular after a singular determiner, because a determiner agrees in
number with its noun (Cunha & Cintra, Nova Gramática do Português Contemporâneo, cap. 9):
"o pais" is "o país", "os pais" stays. A capitalised word inside a sentence is a name
(AO1990 Base XIX 2º a) and b)) and stays as written. The tags are (word, UPOS) pairs,
built here by hand in the shape spaCy gives them, with contractions split (do -> de o).
"""
import pytest

from desacordo_ortografico import OrthographyConverter, convert


def _tags(sentence, **tagged):
    """Tag each word of ``sentence`` as X, except the words given as keyword arguments."""
    words = sentence.replace(".", " .").split()
    return [(w, tagged.get(w.lower(), "X")) for w in words]


# Bare spelling before 1911 -> modern noun or adjective, with the AO1990 clause
NOMINAL = [
    ("historia", "história"),    # Base XI 1º b), apparent proparoxytone in -ia (glória)
    ("agua", "água"),            # Base XI 1º b), apparent proparoxytone in -ua (língua)
    ("familia", "família"),      # Base XI 1º b), apparent proparoxytone in -ia
    ("musica", "música"),        # Base XI 1º a), proparoxytone (músico)
    ("republica", "república"),  # Base XI 1º a), proparoxytone (público)
    ("pagina", "página"),        # Base XI 1º a), proparoxytone
    ("pratica", "prática"),      # Base XI 1º a), proparoxytone (plástico)
    ("funcionaria", "funcionária"),  # Base XI 1º b), apparent proparoxytone in -ia
]


@pytest.mark.parametrize("bare,accented", NOMINAL)
def test_noun_tag_restores_the_accent(bare, accented):
    text = f"A {bare} ficou."
    assert convert(text, "etymological", "pt_1973", pos_tags=_tags(text, **{bare: "NOUN"})) == f"A {accented} ficou."


@pytest.mark.parametrize("bare,accented", NOMINAL)
def test_untagged_form_stays_as_written(bare, accented):
    text = f"A {bare} ficou."
    assert convert(text, "etymological", "pt_1973") == text


def test_adjective_tag_restores_the_accent():
    # contínua: Base XI 1º b), apparent proparoxytone in -ua
    text = "Era uma linha continua."
    tags = _tags(text, continua="ADJ")
    assert convert(text, "etymological", "pt_1973", pos_tags=tags) == "Era uma linha contínua."


@pytest.mark.parametrize("text,word", [
    ("Ele pratica desporto.", "pratica"),       # praticar, presente: ele pratica
    ("A febre continua alta.", "continua"),     # continuar, presente: ele continua
    ("Talvez ele cante amanhã.", "cante"),      # cantar, conjuntivo: que ele cante
    ("Ele leria o livro.", "leria"),            # ler, condicional: ele leria
    ("Assim funcionaria melhor.", "funcionaria"),  # funcionar, condicional: ele funcionaria
])
def test_verb_tag_keeps_the_verb_form(text, word):
    assert convert(text, "etymological", "pt_1973", pos_tags=_tags(text, **{word: "VERB"})) == text


@pytest.mark.parametrize("text", [
    "As antigas casas ficaram.",   # feminine plural of antigo
    "Comeu tanta fruta.",          # feminine singular of tanto
])
def test_noun_tag_does_not_settle_a_nominal_inflection(text):
    tags = [(w, "ADJ") for w in text.replace(".", " .").split()]
    assert convert(text, "etymological", "pt_1973", pos_tags=tags) == text


@pytest.mark.parametrize("det", [
    "o", "um", "do", "no", "ao", "pelo", "este", "aquele", "naquele", "nenhum", "algum",
    "meu", "cada",
])
def test_singular_determiner_takes_the_singular(det):
    assert convert(f"Vive {det} pais.", "etymological", "pt_1973") == f"Vive {det} país."


@pytest.mark.parametrize("text", [
    "Os pais chegaram.",
    "Vieram uns pais.",
    "A casa dos pais.",
    "Ama os seus pais e meus pais.",
    "Ama pais e filhos.",
])
def test_plural_or_no_determiner_keeps_the_plural(text):
    assert convert(text, "etymological", "pt_1973") == text


def test_singular_determiner_with_noun_tag_on_plural_keeps_the_plural():
    # a NOUN tag says nothing about number: "os pais" stays whatever the tag
    text = "Os pais chegaram."
    assert convert(text, "etymological", "pt_1973", pos_tags=_tags(text, pais="NOUN")) == text


def test_determiner_in_the_previous_sentence_does_not_count():
    assert convert("Vi o. Pais chegaram.", "etymological", "pt_1973") == "Vi o. Pais chegaram."


def test_lilac_after_a_determiner():
    # lilás, noun, the shrub (Dicionário Priberam)
    assert convert("O lilas floriu.", "etymological", "pt_1973") == "O lilás floriu."


def test_capitalised_word_inside_a_sentence_is_a_name():
    assert convert("Fui a Coimbra e a Roma.", "etymological", "pt_1973") == "Fui a Coimbra e a Roma."


def test_lowercase_word_takes_the_accent():
    # romã, the fruit: the same letters as Roma, so only the capital tells them apart
    assert convert("Comeu uma roma madura.", "etymological", "pt_1973") == "Comeu uma romã madura."


def test_tags_align_across_split_contractions():
    text = "A historia do pais e da musica."
    tags = [("A", "DET"), ("historia", "NOUN"), ("de", "ADP"), ("o", "DET"), ("pais", "NOUN"),
            ("e", "CCONJ"), ("de", "ADP"), ("a", "DET"), ("musica", "NOUN"), (".", "PUNCT")]
    assert convert(text, "etymological", "pt_1973", pos_tags=tags) == "A história do país e da música."


def test_tags_align_in_order():
    text = "Ele pratica a pratica."
    tags = [("Ele", "PRON"), ("pratica", "VERB"), ("a", "DET"), ("pratica", "NOUN"), (".", "PUNCT")]
    assert convert(text, "etymological", "pt_1973", pos_tags=tags) == "Ele pratica a prática."


def test_tags_align_ignoring_case():
    text = "Historia antiga."
    tags = [("historia", "NOUN"), ("antiga", "ADJ"), (".", "PUNCT")]
    assert convert(text, "etymological", "pt_1973", pos_tags=tags) == "História antiga."


def test_unmatched_tags_leave_the_words_untagged():
    text = "A historia ficou."
    tags = [("Outra", "DET"), ("frase", "NOUN"), (".", "PUNCT")]
    assert convert(text, "etymological", "pt_1973", pos_tags=tags) == text


def test_converter_method_takes_tags():
    text = "A musica ficou."
    result = OrthographyConverter().convert(text, "etymological", "pt_1973", pos_tags=_tags(text, musica="NOUN"))
    assert result.text == "A música ficou."
