"""The 1911 accent guess reads the word before a bare form and the part-of-speech tags.

A bare form that only a verb inflection makes a word takes its accent after a
determiner or a preposition: "a sua historia" is "a sua história", "ele pratica" stays
(Dicionário Priberam, conjugation of falar: ele fala). A bare article counts by
variety (Cunha & Cintra, Nova Gramática do Português Contemporâneo, cap. 11,
pp. 323-331): in Portugal unless a word such as não comes before it, in Brazil only at
the start of a sentence or after a preposition; elsewhere it is a clitic pronoun and
the form stays a verb. Where that rule decides neither, a NOUN or ADJ tag does. A bare form that only a plural makes a word takes its
accented singular after a singular determiner, because a determiner agrees in number
with its noun (cap. 9): "o pais" is "o país", "os pais" stays. A capitalised word
inside a sentence is a name (AO1990 Base XIX 2º a) and b)) and stays as written. The
tags are (word, UPOS) pairs built here by hand. The contractions come split
(do -> de o), as tugatagger's Stanza engine returns them.
"""
import pytest

from desacordo_ortografico import OrthographyConverter, convert
from desacordo_ortografico.lexicon import _inflection_kinds
from desacordo_ortografico.rules import align_tags


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


@pytest.mark.parametrize("target", ["pt_1973", "br_1971"])
@pytest.mark.parametrize("bare,accented", NOMINAL)
def test_determiner_restores_the_noun(bare, accented, target):
    assert convert(f"Leu a sua {bare}.", "etymological", target) == f"Leu a sua {accented}."


@pytest.mark.parametrize("target", ["pt_1973", "br_1971"])
@pytest.mark.parametrize("prep", ["de", "com", "sem", "sobre"])
def test_preposition_restores_the_noun(prep, target):
    assert convert(f"Falou {prep} historia.", "etymological", target) == f"Falou {prep} história."


def test_european_article_counts_unless_a_proclisis_word_comes_first():
    # cap. 11 p. 324: "não", "nunca" put the clitic before the verb; "a" is then the pronoun
    assert convert("Ele estudou a historia.", "etymological", "pt_1973") == "Ele estudou a história."
    assert convert("Ele nunca a pratica.", "etymological", "pt_1973") == "Ele nunca a pratica."
    assert convert("Ele não a pratica.", "etymological", "pt_1973") == "Ele não a pratica."


def test_brazilian_article_counts_at_sentence_start_or_after_a_preposition():
    # cap. 11 pp. 330-331: in Brazil the clitic comes before the verb in main clauses
    assert convert("A historia acabou.", "etymological", "br_1971") == "A história acabou."
    assert convert("Falou sobre a historia.", "etymological", "br_1971") == "Falou sobre a história."
    assert convert("Ele estudou a historia.", "etymological", "br_1971") == "Ele estudou a historia."


@pytest.mark.parametrize("bare,accented", NOMINAL)
def test_noun_tag_restores_the_accent(bare, accented):
    text = f"Estudou {bare} ontem."
    assert convert(text, "etymological", "pt_1973", pos_tags=_tags(text, **{bare: "NOUN"})) == f"Estudou {accented} ontem."


@pytest.mark.parametrize("bare,accented", NOMINAL)
def test_untagged_form_stays_as_written(bare, accented):
    text = f"Estudou {bare} ontem."
    assert convert(text, "etymological", "pt_1973") == text


def test_a_tag_does_not_override_the_rule():
    # a wrong VERB tag after a determiner: the determiner decides
    text = "Leu a sua pratica."
    assert convert(text, "etymological", "pt_1973", pos_tags=_tags(text, pratica="VERB")) == "Leu a sua prática."


def test_a_tag_does_not_override_a_clitic_pronoun():
    # "não a pratica": "a" is the pronoun after "não" (cap. 11 p. 324), so a NOUN tag
    # on "pratica" does not give the accent; with no clitic before it, the tag does
    text = "Ele não a pratica."
    assert convert(text, "etymological", "pt_1973", pos_tags=_tags(text, pratica="NOUN")) == text
    text = "Ele estudou a historia."
    assert convert(text, "etymological", "br_1971", pos_tags=_tags(text, historia="NOUN")) == text
    text = "Ele estudou historia."
    assert convert(text, "etymological", "br_1971", pos_tags=_tags(text, historia="NOUN")) == "Ele estudou história."


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


def test_preposition_a_does_not_take_the_singular():
    # bare "a" before a plural is the preposition: "deu presentes a pais" (to parents)
    assert convert("Vive o pais.", "etymological", "pt_1973") == "Vive o país."
    assert convert("Dei presentes a pais e filhos.", "etymological", "pt_1973") == "Dei presentes a pais e filhos."


def test_noun_ar_is_no_infinitive():
    # the conditional is a stem + -ar/-er/-ir + ia (ler -> leria); the noun ar has no stem
    assert _inflection_kinds("leria", {"ler"}) == {"verb"}
    assert _inflection_kinds("aria", {"ar"}) == frozenset()


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
    text = "Saiu do teatro e estudou musica."
    tags = [("Saiu", "VERB"), ("de", "ADP"), ("o", "DET"), ("teatro", "NOUN"), ("e", "CCONJ"),
            ("estudou", "VERB"), ("musica", "NOUN"), (".", "PUNCT")]
    assert convert(text, "etymological", "pt_1973", pos_tags=tags) == "Saiu do teatro e estudou música."


def test_tags_align_past_a_word_split_in_several_tokens():
    # the tagger splits "guarda-chuva" into three tokens and "da" into two, so the tag of
    # "musica" sits five places past the last match
    tags = [("O", "DET"), ("guarda", "NOUN"), ("-", "PUNCT"), ("chuva", "NOUN"), ("de", "ADP"),
            ("a", "DET"), ("musica", "ADJ"), (".", "PUNCT")]
    words = ["O", "guarda-chuva", "da", "musica"]
    assert align_tags(words, tags) == ["DET", None, None, "ADJ"]


def test_tags_do_not_reach_a_far_word_of_the_same_spelling():
    # the tagger did not return the first "pratica"; it must not take the tag of the
    # second one, ten places ahead
    text = "Ele pratica um dois tres quatro cinco seis sete oito nove pratica."
    tags = [("Ele", "PRON"), ("praticava", "VERB")] + [(w, "NUM") for w in text.split()[2:-1]]
    tags += [("pratica", "NOUN"), (".", "PUNCT")]
    words = text.rstrip(".").split()
    assert align_tags(words, tags) == ["PRON", None] + ["NUM"] * 9 + ["NOUN"]


def test_tags_align_in_order():
    text = "Ele pratica a pratica."
    tags = [("Ele", "PRON"), ("pratica", "VERB"), ("a", "DET"), ("pratica", "NOUN"), (".", "PUNCT")]
    assert convert(text, "etymological", "pt_1973", pos_tags=tags) == "Ele pratica a prática."


def test_tags_align_ignoring_case():
    text = "Historia antiga."
    tags = [("historia", "NOUN"), ("antiga", "ADJ"), (".", "PUNCT")]
    assert convert(text, "etymological", "pt_1973", pos_tags=tags) == "História antiga."


def test_unmatched_tags_leave_the_words_untagged():
    text = "Estudou historia ontem."
    tags = [("Outra", "DET"), ("frase", "NOUN"), (".", "PUNCT")]
    assert convert(text, "etymological", "pt_1973", pos_tags=tags) == text


def test_converter_method_takes_tags():
    text = "Estudou musica ontem."
    result = OrthographyConverter().convert(text, "etymological", "pt_1973", pos_tags=_tags(text, musica="NOUN"))
    assert result.text == "Estudou música ontem."
