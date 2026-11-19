"""Deterministic, regular orthographic transforms (the regex-able rules).

These are the transforms that do *not* need a lexicon: Greek-digraph simplification
(1911), the open/closed nasal-vowel alternation (PT<->BR), the AO1990 accent drops,
trema abolition, month lowercasing and the AO1990 prefix joins.

Each function takes and returns a **lowercase** word; case restoration is handled by
:func:`apply_to_words`, which also tokenises the text. Functions are grouped by the
reform that introduced them and are documented as *reversible* (a clean inverse exists)
or *one-way* (the inverse is ambiguous and must be resolved by a lexicon upstream).

The 1911 accent guess (:func:`guess_accents`) reads the word before each bare form.
The sources are Cunha & Cintra, *Nova Gramática do Português Contemporâneo*, 7.ª ed.,
Lexikon 2017, and the AO1990 text.

- A determiner or a preposition introduces a noun phrase: the article and the
  determiners agree with the noun (cap. 9 "Artigo", p. 219; cap. 11 "Pronomes",
  p. 289), and a preposition relates a term to its consequent (cap. 15 "Preposição",
  pp. 569-570). The contractions with the indefinite article (num, duma; cap. 9,
  pp. 223-224) and the classical polo, pola (p. 223) count as determiners. After one
  of them, a bare form that is otherwise only a verb form is
  the noun: "a sua historia" is "a sua história".
- The bare articles o, a, os and as are also the clitic pronouns. In Portugal the
  clitic follows the verb unless a word such as não, que, já or quando comes before
  it (cap. 11, "Colocação dos pronomes átonos", pp. 323-327): a negative word
  (não, nunca, jamais, ninguém, nada), an interrogative, one of the adverbs bem, mal,
  ainda, já, sempre, só, talvez, or the subject alguém. So a bare article
  counts unless such a word stands right before it. In Brazil the clitic comes before the verb
  in main clauses too (cap. 11, "A colocação dos pronomes átonos no Brasil",
  pp. 330-331), so a bare article counts only at the start of a sentence or clause or after a
  preposition. A pause ends the context, because these words put the clitic first only
  "quando entre ela e o verbo não há pausa" (p. 324): the word before a comma, a
  colon, a parenthesis or a dash decides nothing about the word after it. Brackets are
  no pause: they hold remarks an author adds inside a transcribed text ("Pontuação",
  p. 681: "numa transcrição de texto alheio, o autor intercala observações próprias").
- The article and the determiners agree in number with the noun, so after a singular
  determiner a bare form that is otherwise only a plural is the singular noun:
  "o pais" is "o país".
- A capitalised word takes the accent of the common word with the same letters, so
  names whose 1973 spelling carries an accent come back right (Árctico, Atlântico,
  Sibéria). A capital marks a name (AO1990 Base XIX 2º b): the city names in
  ``_UNACCENTED_NAMES``, which share their letters with an accented common word
  (Roma, romã), stay as written when capitalised.

The edges out of 1911 take a word in the spelling of the Formulário Ortográfico of 1911
to the Portuguese norm of 1945 and to the Brazilian norm of 1943. The 1945 rules quote the
Acordo Ortográfico of 1945 (Portal da Língua Portuguesa: the Conclusões complementares and
the Bases Analíticas), and the 1943 rules quote the Formulário Ortográfico of 1943 (Academia
Brasileira de Letras).

- An oxytone of more than one syllable in -êm or -êns takes the acute. 1911 Base XIV:
  "Os vocábulos terminados no ditongo em (equivalente a ẽi) receberão o acento
  circunflexo quando forem polissilabos com a última sílaba predominante. [...] contêm, do
  verbo conter". 1945 Base XIII: "amém (variação de ámen), armazém, convém, mantém,
  ninguém, porém, Santarém, também; convêm, mantêm, têm (3.ª pessoas do plural);
  armazéns, desdéns, convéns, reténs". 1943, 7.ª: "Marca-se com o acento agudo o e da
  terminação em ou en das palavras oxítonas de mais de uma sílaba: alguém, armazém,
  convém, convéns, detém-lo, mantém-na, parabéns, retém-no, também, etc." The 1911 contêm
  is the singular of conter, but the compounds of ter and vir stay as written: from 1945
  on the same letters spell the plural. Conclusões complementares of 1945, 20: "têm, vêm,
  contêm, convêm, etc., graficamente distintas das terceiras pessoas do singular
  correspondente - tem, vem, contém, convém, etc. Essas formas terão emprego exclusivo na
  escrita corrente, preterindo assim as flexões têem, contêem, convêem, etc." A text that
  passes through 1911 on its way between the Portuguese and the Brazilian norms carries
  that plural (mantêm), and the letters alone cannot tell it from the 1911 singular.
- The 1911 grave on a u after q or g goes. 1911 Base XLVI: "fre qùente, a gùentar, ar
  gùir". 1945 Base XXVII: "abstrai-se de sinal especial, [...] para distinguir, em sílaba
  tónica ou átona, o u de gu ou qu de um e ou i seguintes: [...] aguentar, [...] arguir,
  [...] frequentar, tranquilo". 1943 writes the trema instead, 12.ª: "Emprega-se o trema
  no u que se pronuncia depois de g ou q e seguido de e ou i: agüentar, argüição,
  eloqüente, tranqüilo, etc."
- The initial sc loses its s in the words that 1911 Base XI names, with their derivatives:
  "É conservado o grupo inicial sc, das seguintes palavras e seus derivados e afins, em que
  o s é mudo: scena, sciência, scetro, scéptico, scisma, scisão, sciático, scintilar,
  scelerado, e algum outro menos usual". A foreign word outside these families keeps its
  sc (Science); an English word inside them (scientific, sceptical) loses it. The Bases of
  1931, § 1.º, drop the s: "Eliminar: [...] 4.º O s do grupo inicial: ciência, ciática".
  The decree of 1945 says Portugal adopted the 1931 accord: "foi aprovado e mandado
  executar, em Portugal pela portaria n.o 7:117, de 27 de Maio do mesmo ano". 1943, 19.:
  "Elimina-se o s do grupo inicial sc: celerado, cena, cenografia, ciência, cientista,
  cindir, cintilar, ciografia, cisão, etc."
- 1945 drops the circumflex that tells a closed e or o from an open one, the accent of
  1911 Base XXVIII ("marcar-se hão êstes com o acento circunflexo"). 1945 Base XXII: "O
  emprego do acento circunflexo, para distinguir formas paroxítonas ou oxítonas das suas
  homógrafas heterofónicas, faz-se apenas em dois casos", with the forms that keep it: côa,
  côas, pêlo, pêlos, pêra, pêro, pôlo, pôlos, pôr, pôde and dêmos. "Feita esta limitação,
  prescinde-se do acento circunflexo [...]: [...] ele (ê), pronome, [...] este (ê),
  pronome". Base XXI keeps it in the hiatus ee ("crêem, dêem, lêem, vêem") and drops it in
  the hiatus oo ("abençoo, condoo-me, enjoo, moo, remoo, voos"). 1943 keeps the 1911
  accent, 14.ª: "Emprega-se o acento circunflexo como diferencial ou distintivo no e e no
  o fechados da sílaba tônica das palavras que estão em homografia com outras em que são
  abertos êsse e e êsse o".
  The 1911 circumflex marks one of two homographs. 1911 Base XXVIII: "Quando um qualquer
  vocábulo que tenha por sílaba predominante a penúltima, e cuja vogal nessa sílaba seja e
  ou o abertos, fôr homógrafo com outro em que êsse e ou o seja fechado, marcar-se hão êstes
  com o acento circunflexo". So the accent goes only where the bare letters spell a
  Portuguese word: a word of the word list as written, accents and all, a contraction of
  de or em with one (dêste, 1911 Base XXXVIII), or a regular form of a known verb (vivêra,
  perdôa). A pre-1911 shape that the etymological edge leaves stays. The bare letters of
  aldêa and pôz-se spell no word of the list. In fêl-o and vêl-a the r, s or z of the verb
  became l before the pronoun, which 1911 Base XXXIV calls an error: "São erros
  inadmissíveis, mas muito freqùentes, louval-o, devel-o, punil-o". The bare part fel is a
  word, so a part that ends in l before the hyphen and o, a, os or as keeps its accent. A
  foreign word whose bare letters spell no Portuguese word stays (prêtres, être). A foreign
  word whose bare letters spell a listed word loses its accent: Côte, tête and pôle as in
  French, and the loans crêpe, cône and contrôle as 1945 writes them (crepe, cone,
  controle). A 1945 word that the list lacks keeps its accent (môo, vêde, tôrvo).

AO1990 drops the acute of the open diphthongs éi and ói in paroxytones only. Base IX 3º:
"Não se acentuam graficamente os ditongos representados por ei e oi da sílaba
tónica/tônica das palavras paroxítonas [...]: assembleia, boleia, ideia, [...] heroico,
introito, jiboia, moina, paranoico, zoina." Base XI 1º keeps it in proparoxytones, real
and apparent: "a) As palavras proparoxítonas que apresentam na sílaba tónica/tônica as
vogais abertas grafadas a, e, o e ainda i, u ou ditongo oral começado por vogal aberta"
and "b) As chamadas proparoxítonas aparentes, [...] que terminam por sequências vocálicas
pós-tónicas/pós-tônicas praticamente consideradas como ditongos crescentes (-ea, -eo,
-ia, -ie, -io, -oa, -ua, -uo, etc.)". So the accent goes only when one syllable follows
the diphthong, and a final -ea, -eo, -ia, -ie, -io, -oa, -ua or -uo counts as two:
alantóideo (a-lan-tói-de-o) and einstéinio keep it. Each part of a hyphenated word has
its own stress, Base XV 1º: "cujos elementos [...] constituem uma unidade sintagmática e
semântica e mantêm acento próprio". The oxytone parts of rói-rói and
ascídia-de-anéis-brancos keep their accent. Base IX 2º a) gives the acute before -l, -n,
-r, -x and -ps to "as vogais abertas grafadas a, e, o e ainda i ou u" and names no
diphthong, so the text has no exception for destróier.

The words that no rule reaches are rows of the spelling table (quási, tam, teem, and
scetro, which 1945 Base VI writes ceptro), each with its clause. The rows apply to each
part of a hyphenated word, except in a word whose parts repeat (tam-tam, a gong).
"""
from __future__ import annotations

import re
import unicodedata
from typing import Callable, Collection, List, Mapping, Optional, Sequence, Tuple

from .lexicon import _ACCENTS, deaccent

# letters that count as part of a word (ASCII + Latin-1 accented range)
_WORD_RE = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[-'’][0-9A-Za-zÀ-ɏ]+)*")
_VOWELS = "aeiouáàâãéêíóôõúü"
# the joints of a compound word: hyphen and apostrophes
_SEGMENT_SEP = re.compile(r"[-'’]")


# ----------------------------------------------------------------- tokenising
def apply_to_words(
    text: str,
    fn: Callable[[str], str],
    is_word: Optional[Callable[[str], bool]] = None,
) -> str:
    """Apply ``fn`` to each word in ``text``, preserving case and punctuation.

    ``fn`` receives a lowercase word and returns a lowercase word; the original
    capitalisation pattern (UPPER / Title / lower) is re-applied to the result, per
    hyphen or apostrophe segment (see :func:`_match_case`). A word with a capital
    inside a segment and not in capitals throughout (pH, kW, McDonald, TVs) is a symbol
    or a name, not a lowercase word, and none of the three patterns can restore it: it
    is returned as written. When ``is_word`` is given, a word in capitals throughout
    whose lowercase form is no word is an acronym or a symbol, and it stays as written
    (IPTU, PPD, the axis Y; AO1990 Base I 2º c)).
    """
    return map_words(text, lambda _i, word: fn(word), is_word)[0]


def map_words(
    text: str,
    fn: Callable[[int, str], Optional[str]],
    is_word: Optional[Callable[[str], bool]] = None,
) -> Tuple[str, List[int]]:
    """Apply ``fn`` to each word in ``text`` as :func:`apply_to_words` does, and give
    ``fn`` the index of the word in :func:`words` before the word. A word for which
    ``fn`` returns ``None`` stays as written.

    Returns the new text and, for each word of it, the index of the word of ``text``
    that it comes from. One word can become more than one (acha-de-armas -> acha de
    armas), so the indexes of the words after it move.
    """
    out: List[str] = []
    sources: List[int] = []
    last = 0
    for i, match in enumerate(_WORD_RE.finditer(text)):
        word = new = match.group(0)
        symbol = not word.isupper() and any(s[1:] != s[1:].lower() for s in _SEGMENT_SEP.split(word))
        acronym = is_word is not None and word.isupper() and not is_word(word.lower())
        if not symbol and not acronym:
            form = fn(i, word.lower())
            new = word if form is None else _match_case(word, form)
        out += [text[last:match.start()], new]
        sources += [i] if new == word else [i] * len(_WORD_RE.findall(new))
        last = match.end()
    out.append(text[last:])
    return "".join(out), sources


#: A sentence end: the word after it opens a sentence.
_SENTENCE_END = re.compile(r"[.!?…\n]")
#: Abbreviations before a name whose period ends no sentence (o Sr. Silva, a Av. Brasil).
_ABBREVIATIONS = frozenset({"sr", "sra", "srs", "sras", "dr", "dra", "drs", "dras", "av", "d", "s"})


def names(text: str) -> List[bool]:
    """Tell, for each word of :func:`words`, whether it is written as a name: a word
    inside a sentence that starts with a capital, or has a part that does, and is not in
    capitals throughout.

    A word opens a sentence when no word comes before it or a sentence end (. ! ? … or
    a line break) comes between it and the word before it. The period of Sr., Sra., Dr.,
    Dra., Av., D. (Dom, Dona) or S. (São) is no sentence end; a colon or an opening
    quote is none either. A text with
    no word in lowercase gives no case signal, so it has no names.
    """
    matches = list(_WORD_RE.finditer(text))
    if not any(m.group(0).islower() for m in matches):
        return [False] * len(matches)
    out = [False]
    for prev, match in zip(matches, matches[1:]):
        word = match.group(0)
        gap = text[prev.end():match.start()]
        if prev.group(0).lower() in _ABBREVIATIONS:
            gap = gap.removeprefix(".")
        out.append(not _SENTENCE_END.search(gap) and not word.isupper()
                   and any(s[:1].isupper() for s in _SEGMENT_SEP.split(word)))
    return out


def lookup_with_plural(word: str, table: Mapping[str, str]) -> Optional[str]:
    """``table[word]``, or the plural of the table form when ``word`` is the regular
    plural of a table word (aspetos from aspeto, receções from receção, diretores from
    diretor); else ``None``."""
    if word in table:
        return table[word]
    if word.endswith("ões") and word[:-3] + "ão" in table and table[word[:-3] + "ão"].endswith("ão"):
        return table[word[:-3] + "ão"][:-2] + "ões"
    if word.endswith("s") and word[:-1] in table and table[word[:-1]][-1:] in "aeo":
        return table[word[:-1]] + "s"
    if word.endswith("es") and word[:-2] in table and table[word[:-2]].endswith(("or", "z")):
        return table[word[:-2]] + "es"
    return None


def words(text: str) -> List[str]:
    """Return the list of word tokens in ``text`` (original case)."""
    return _WORD_RE.findall(text)


def _match_case(original: str, transformed: str) -> str:
    """Re-apply the case of ``original`` to ``transformed``.

    A compound with a capital after a hyphen or an apostrophe (Trás-os-Montes, d'Arga)
    takes the case of each segment. When the segments join (Anti-Semitismo ->
    antissemitismo), the result takes the case of the first segment.
    """
    if original.isupper() and len(original) > 1:
        return transformed.upper()
    segments = _SEGMENT_SEP.split(original)
    if any(s[:1].isupper() for s in segments[1:]):
        parts = re.split(r"([-'’])", transformed)
        if len(parts[::2]) != len(segments):
            return _match_case(segments[0], transformed)
        parts[::2] = [_match_case(s, p) for s, p in zip(segments, parts[::2])]
        return "".join(parts)
    if original[:1].isupper():
        return transformed[:1].upper() + transformed[1:]
    return transformed


# ----------------------------------------------------- Reforma de 1911 (digraphs)
#: ⟨ch⟩ of [k] in words of Greek origin. 1911 replaced ⟨ch⟩ "com valor de [k]" by ⟨c⟩
#: or ⟨qu⟩ (Reforma Ortográfica de 1911, the digraphs of Greek origin). In these words
#: ⟨ch⟩ before ⟨r⟩, ⟨l⟩, ⟨n⟩ or ⟨th⟩ is [k] and becomes ⟨c⟩: christianismo, chloro,
#: technica, ichthyologia. ⟨ch⟩ before other consonants and after ⟨s⟩ is left alone,
#: because loanwords and names use it for other sounds (sandwichs, Utrecht, Richmond,
#: Schmidt). Before a vowel the word map decides. Names that match still change, as
#: they do under ph, th and y: Christina gives Cristina.
_CH_K_RE = re.compile(r"(?<!s)ch(?=[rln]|th)")


def reform_1911_digraphs(word: str) -> str:
    """ch->c before r, l, n or th, then ph->f, th->t, rh->r, y->i. Reversible? No — the
    inverse is ambiguous."""
    word = _CH_K_RE.sub("c", word)
    word = word.replace("ph", "f").replace("th", "t").replace("rh", "r")
    word = word.replace("y", "i")
    return word


# The 1911 Formulário reforms the spelling of "todas as palavras portuguesas, ou
# aportuguesadas": I proscribes k, w and y in them, and II writes them "sómente com umas
# ou com outras" of its letters. A loanword or a foreign name is neither, so the 1911
# rule fallbacks leave it alone. Its derivatives keep its letters too: Formulário I,
# Exceção 1.ª, "Poderão usar-se essas letras em vocábulos derivados de nomes próprios
# estrangeiros"; the Bases Analíticas of the Acordo of 1945, 1, "byroniano, taylorista",
# and 2, "quaisquer combinações gráficas não peculiares à nossa escrita".
# A word carries the spelling of a loanword or a foreign name when it has k or w, zz,
# sh, y before a vowel at the start, a final pair of consonants other than ch, ph, th
# and cc (Clifford, Scott, Through), or a ü that follows neither g, q nor a vowel
# (mülleriano, of Müller; Portuguese writes ü only after g or q or on a hiatus). These
# are no such spelling:
# - a single final consonant: AO1990 Base I 5º keeps it in names of the biblical
#   tradition ("Jacob, Job, Moab, Isaac, David, Gad; Gog, Magog; Bensabat, Josafat"),
#   and an abbreviation ends in one (Typ., Rhet.);
# - the final digraphs ch, ph and th: Base I 4º, "Baruch, Loth, Moloch, Ziph" (Math.,
#   Orth.); and final cc, which pre-1911 Portuguese writes in Occ. (occidental);
# - final -ie: Portuguese writes it (espécie, série, anuncie);
# - a y inside or at the end of a word: pre-1911 Portuguese writes it (Bayão, Moreyra,
#   Jayme, Piauhy), and no spelling tells taylorista or byroniano from Baylão or Froylas.
_FOREIGN_RE = re.compile(
    r"[kw]|zz|sh|^y[aeiou]"
    r"|(?!cc$|[cpt]h$)[^aeiouáàâãéêíóôõúüy][^aeiouáàâãéêíóôõúüylrszmnx]$"
    r"|(?<![gqaeiouáàâãéêíóôõú])ü")


def is_foreign_spelling(word: str) -> bool:
    """True when ``word`` carries a letter or cluster of a loanword or foreign name."""
    return bool(_FOREIGN_RE.search(word))


# --------------------------------------------------- Reforma de 1911 (geminates)
_GEMINATE_RE = re.compile(r"([bcdfgjlmnpqtvz])\1")


def reform_1911_geminates(word: str, wordset=None) -> str:
    """Reduce a doubled consonant to a single one, the way 1911 did.

    Etymological geminates (anno, commando, collectiva, sufficiente) collapse, but the
    etymological ``rr``/``ss`` survive in modern spelling (carro, passo) and are excluded
    from the character class. ``mm``/``nn`` also survive in a few modern PT words
    (connosco, comummente), so when a word list is supplied a word already in it is left
    untouched. Applied as a rule fallback so inflections the lexicon omits are handled.
    One-way.
    """
    if wordset is not None and word in wordset:
        return word
    return _GEMINATE_RE.sub(r"\1", word)


#: The sequences of Base IV 1º: "cc (segundo c com valor de sibilante), cç e ct" and
#: "pc (c com valor de sibilante), pç e pt", each with the c or the p dropped.
_CP_DROP = [("cc", "c"), ("cç", "ç"), ("ct", "t"), ("pc", "c"), ("pç", "ç"), ("pt", "t")]


def drop_silent_cp(word: str, table: Mapping[str, str]) -> str:
    """Drop a silent c/p from a Base IV 1º sequence (AO1990, European), for the regular
    plural of a word the AO1990 map ``table`` lists (actos -> atos).

    Whether the consonant is silent is a fact about each word: Base IV 1º a keeps it
    where the cultivated pronunciation says it (apto, rapto) and 1º b drops it where it
    is mute (ato, ótimo). So the step drops only the consonant the map drops, and a word
    the map does not hold stays as written: dropping a pronounced consonant gives another
    word (apta -> ata, copta -> cota). One-way.
    """
    form = lookup_with_plural(word, table)
    return form if form is not None and _drops_cp(word, form) else word


def restore_silent_cp(word: str, table: Mapping[str, str]) -> str:
    """The inverse of :func:`drop_silent_cp`, for the regular plural of a word the
    reverse AO1990 map ``table`` lists (atos -> actos). One-way."""
    form = lookup_with_plural(word, table)
    return form if form is not None and _drops_cp(form, word) else word


def _drops_cp(old: str, new: str) -> bool:
    """True when ``new`` is ``old`` without the c or p of a Base IV 1º sequence."""
    return any(old.replace(pat, rep) == new for pat, rep in _CP_DROP)


#: The determiners other than the bare articles: the contractions of a preposition and
#: an article, and the demonstratives, possessives and indefinites. See the module
#: docstring.
_DETERMINERS = frozenset({
    "do", "da", "dos", "das", "no", "na", "nas", "ao", "aos", "à", "às",
    "pelo", "pela", "pelos", "pelas", "um", "uma", "uns", "umas",
    "este", "esta", "estes", "estas", "esse", "essa", "esses", "essas",
    "aquele", "aquela", "aqueles", "aquelas", "deste", "desta", "destes", "destas",
    "desse", "dessa", "daquele", "daquela", "neste", "nesta", "nesse", "nessa",
    "naquele", "naquela", "meu", "minha", "teu", "tua", "seu", "sua", "nosso", "nossa",
    "vosso", "vossa", "meus", "minhas", "teus", "tuas", "seus", "suas", "nossos", "nossas",
    "vossos", "vossas", "cada", "nenhum", "nenhuma", "algum", "alguma",
    "outro", "outra", "todo", "toda",
    "num", "numa", "nuns", "numas", "dum", "duma", "duns", "dumas",
    "polo", "pola", "polos", "polas",
})
#: The bare articles, which are also the clitic pronouns.
_ARTICLES = frozenset({"o", "a", "os", "as"})
#: Words that put a clitic pronoun before the verb in European Portuguese, unaccented.
#: ambos, todo, tudo, outro and qualquer (cap. 11 p. 327) are left out: p. 327 needs them in
#: the subject, and right before an article they are mostly determiners or objects
#: (todas as casas, ambos os lados, reduzia tudo a fórmulas).
_PROCLISIS_TRIGGERS = frozenset({
    "que", "nao", "se", "ja", "nunca", "sempre", "tambem", "so", "quem", "ainda", "bem",
    "mal", "talvez", "onde", "quando", "como", "porque", "embora",
    "jamais", "ninguem", "nada", "alguem",
})
#: The simple prepositions of cap. 15, unaccented, except a, which is also the article.
_PREPOSITIONS = frozenset({
    "ante", "apos", "ate", "com", "contra", "de", "desde", "em", "entre", "para", "perante",
    "por", "sem", "sob", "sobre", "tras",
})
#: The determiners that mark a singular noun, see the module docstring. Bare "a" is
#: left out because it is also the preposition ("deu presentes a pais").
_SINGULAR_DETERMINERS = frozenset({
    "o", "um", "uma", "do", "da", "no", "na", "ao", "à", "pelo", "pela",
    "num", "numa", "dum", "duma", "polo", "pola",
    "este", "esta", "esse", "essa", "aquele", "aquela", "deste", "desta",
    "neste", "nesta", "naquele", "naquela", "nenhum", "nenhuma", "algum", "alguma",
    "meu", "minha", "teu", "tua", "seu", "sua", "nosso", "nossa", "vosso", "vossa",
    "cada",
})
#: The universal POS tags of a noun or an adjective.
_NOMINAL_TAGS = frozenset({"NOUN", "ADJ"})
# names written without an accent whose letters spell an accented common word: the cities
# Coimbra (coimbrã) and Roma (romã), and the given name Ester (éster). ABL Pequeno
# Vocabulário Ortográfico 1943: "éster, s. m./Cf. Ester, antr., e hester."
_UNACCENTED_NAMES = frozenset({"coimbra", "roma", "ester"})
# a sentence end or a clause pause; the word before it does not introduce the next word
_PAUSE = re.compile(r"[.!?…,;:()—–]|\s-\s")
#: How many tags past the last match a word may look for its own. A tagger can split
#: one word into a few tokens (Stanza splits do into de o); the bound keeps a word the
#: tagger did not return from taking the tag of the same spelling far ahead.
_TAG_LOOKAHEAD = 8


def align_tags(words: List[str], pos_tags: Sequence[Tuple[str, str]]) -> List[Optional[str]]:
    """Give each word the tag of the next ``(word, tag)`` pair with the same spelling.

    Words and pairs are matched in order, ignoring case. A word with no matching pair,
    such as "do" when Stanza split it into "de" and "o", gets ``None``.
    """
    tags: List[Optional[str]] = []
    j = 0
    for word in words:
        low = word.lower()
        tag = None
        for k in range(j, min(j + _TAG_LOOKAHEAD, len(pos_tags))):
            if pos_tags[k][0].lower() == low:
                tag, j = pos_tags[k][1], k + 1
                break
        tags.append(tag)
    return tags


def _starts_noun_phrase(prev: Optional[str], before: Optional[str], variety: str) -> Optional[bool]:
    """Tell whether the word ``prev``, after the word ``before``, introduces a noun phrase.

    ``True``: a determiner, a preposition, or a bare article that counts as the article.
    ``False``: a bare article that is a clitic pronoun, so the next word is a verb.
    ``None``: any other word, or no word; the context does not decide. ``prev`` and
    ``before`` are lowercase and ``None`` past the start of the sentence or clause. ``variety`` is
    "pt" or "br"; see the module docstring.
    """
    if prev is None:
        return None
    if prev in _DETERMINERS or deaccent(prev) in _PREPOSITIONS:
        return True
    if prev not in _ARTICLES:
        return None
    if variety == "br":
        return before is None or deaccent(before) in _PREPOSITIONS
    return before is None or deaccent(before) not in _PROCLISIS_TRIGGERS


def guess_accents(
    text: str,
    restore: Mapping[str, str],
    nominal: Mapping[str, str],
    singular: Mapping[str, str],
    tags: Sequence[Optional[str]],
    variety: str = "pt",
    hold: Collection[int] = (),
) -> str:
    """Re-supply the graphic accent 1911 introduced (fosforo -> fósforo).

    A word that carries no accent takes the accented form from ``restore``. It takes it
    from ``nominal`` when the word before it introduces a noun phrase in ``variety``
    ("pt" or "br"): a sua historia -> a sua história. When the word before it is a clitic
    pronoun, the form is a verb and stays. When the word before it decides neither, a
    NOUN or ADJ tag gives the accent. It
    takes it from ``singular`` after a singular determiner (o pais -> o país). ``tags``
    holds one tag or ``None`` per word of ``text``. The words whose index in
    :func:`words` is in ``hold`` stay as written. Case-preserving.
    """
    matches = list(_WORD_RE.finditer(text))
    if len(matches) != len(tags):
        raise ValueError(f"{len(tags)} tags for {len(matches)} words")
    starts = [i == 0 or bool(_PAUSE.search(text, matches[i - 1].end(), m.start()))
              for i, m in enumerate(matches)]
    out: List[str] = []
    last = 0
    for i, (match, tag) in enumerate(zip(matches, tags)):
        word = match.group(0)
        low = word.lower()
        out.append(text[last:match.start()])
        last = match.end()
        prev = None if starts[i] else matches[i - 1].group(0).lower()
        before = None if starts[i] or starts[i - 1] else matches[i - 2].group(0).lower()
        # the tilde and the cedilla are no accents (cap. 4 p. 78-79): orgão, açucar
        accented = not _ACCENTS.isdisjoint(unicodedata.normalize("NFD", low))
        # a capital inside a segment marks a symbol or a name (McDonald, pH)
        symbol = not word.isupper() and any(s[1:] != s[1:].lower() for s in _SEGMENT_SEP.split(word))
        name = word[:1].isupper() and low in _UNACCENTED_NAMES
        form = None
        if not accented and not symbol and not name and i not in hold:
            form = restore.get(low)
            noun = _starts_noun_phrase(prev, before, variety)
            if form is None and (noun if noun is not None else tag in _NOMINAL_TAGS):
                form = nominal.get(low)
            if form is None and prev in _SINGULAR_DETERMINERS:
                form = singular.get(low)
        out.append(word if form is None else _match_case(word, form))
    out.append(text[last:])
    return "".join(out)


# ------------------------------------------------ PT<->BR nasal-vowel alternation
# Stressed open e/o before an intervocalic nasal: PT writes acute, BR circumflex.
# Restricted to m/n FOLLOWED BY A VOWEL so oxytones in -em/-om (tambem, parabens)
# are left untouched.
_NASAL_FOLLOW = "[mn][%s]" % _VOWELS


def nasal_vowel_to_br(word: str) -> str:
    word = re.sub("é(?=%s)" % _NASAL_FOLLOW, "ê", word)  # é -> ê
    word = re.sub("ó(?=%s)" % _NASAL_FOLLOW, "ô", word)  # ó -> ô
    return word


def nasal_vowel_to_pt(word: str) -> str:
    word = re.sub("ê(?=%s)" % _NASAL_FOLLOW, "é", word)  # ê -> é
    word = re.sub("ô(?=%s)" % _NASAL_FOLLOW, "ó", word)  # ô -> ó
    return word


# ---------------------------------------- the edges out of 1911 (BR 1943, PT 1945)
# See the module docstring for the clause of each rule.
# the ê of a final -êm or -êns after a consonant, or after the u of gu or qu
_RE_OXYTONE_EM = re.compile("(?:[^%s]|[gq]u)(ê)(?:m|ns)$" % _VOWELS)
_RE_VOWEL = re.compile("[%s]" % _VOWELS)
_RE_GRAVE_U = re.compile("([gq])ù(?=[eiéíê])")
# the words of 1911 Base XI and their derivatives: scena, sciência, scetro, scéptico,
# scisma, scisão, sciático, scintilar, scelerado
_RE_INITIAL_SC = re.compile(
    "^sc(?=en[aáéo]|iênc|ient|etr|ept|épt|ism|isã|isõ|iát|iat|intil|eler)")
# a closed e or o in the last-but-one syllable before a final -a, -e, -o (with -s), -am,
# -em or -ens, or in the last syllable before a final r, z or l
# a pre-1911 enclitic (fêl-o, vêl-a): 1911 Base XXXIV writes devê-lo
_RE_PRE_1911_ENCLITIC = re.compile(r"l-(?:o|a|os|as)(?=$|-)")
_RE_CIRCUMFLEX = re.compile("(.*)([êô])((?:[^%s]*(?:[aeo]s?|[ae]m|ens))|[rzl])" % _VOWELS)
_KEPT_CIRCUMFLEX_1945 = frozenset({
    "côa", "côas", "pêlo", "pêlos", "pêra", "pêro", "pôlo", "pôlos", "pôr", "pôde", "dêmos"})
# the endings after the accented vowel of a regular verb form: -er and -or verbs
# (vivêra, opôrem, fôssem) and -oar verbs (perdôa, abençôe)
_ER_OR_ENDINGS = frozenset({
    "r", "ra", "ras", "ram", "ramos", "rem", "res", "mos", "sse", "sses", "ssem", "ste", "stes"})
_OAR_ENDINGS = frozenset({"a", "as", "am", "e", "es", "em", "o"})


def per_segment(word: str, fn: Callable[[str], str]) -> str:
    """Apply ``fn`` to each part of a hyphenated or elided word (além-rio, sobr'ôlho)."""
    parts = re.split(r"([-'’])", word)
    parts[::2] = [fn(p) for p in parts[::2]]
    return "".join(parts)


def oxytone_em_acute(word: str) -> str:
    """-êm/-êns -> -ém/-éns in an oxytone of more than one syllable (tambêm -> também,
    armazêns -> armazéns). A compound of ter or vir in -têm or -vêm stays. One-way."""
    def acute(part: str) -> str:
        m = _RE_OXYTONE_EM.search(part)
        if m is None or not _RE_VOWEL.search(part, 0, m.start()):
            return part
        if len(part) > 3 and part.endswith(("têm", "vêm")) and part != "vintêm":  # contêm
            return part
        return part[:m.start(1)] + "é" + part[m.end(1):]

    return per_segment(word, acute)


def grave_u_to_trema(word: str) -> str:
    """qù/gù before e or i -> qü/gü, the 1943 trema (tranqùilo -> tranqüilo). One-way."""
    return _RE_GRAVE_U.sub(r"\1ü", word)


def drop_grave_u(word: str) -> str:
    """qù/gù before e or i -> qu/gu, as 1945 writes them (tranqùilo -> tranquilo). One-way."""
    return _RE_GRAVE_U.sub(r"\1u", word)


def drop_initial_sc(word: str) -> str:
    """Initial sc -> c in the words of 1911 Base XI (sciência -> ciência, scena -> cena,
    scintilava -> cintilava). One-way."""
    return _RE_INITIAL_SC.sub("c", word)


def _is_portuguese(bare: str, accent: int, is_word: Callable[[str], bool]) -> bool:
    """True when ``bare``, a word with its circumflex dropped at ``accent``, is a
    Portuguese word: a listed word, a contraction of de or em with one (deste), or a
    regular form of a listed verb (vivera, opor, perdoa)."""
    if is_word(bare):
        return True
    if bare[0] in "dn" and bare[1:2] in ("a", "e", "o") and is_word(bare[1:]):
        return True
    stem, vowel, ending = bare[:accent], bare[accent], bare[accent + 1:]
    if not stem:
        return False
    if ending in _ER_OR_ENDINGS and is_word(stem + vowel + "r"):
        return True
    return vowel == "o" and ending in _OAR_ENDINGS and is_word(stem + "oar")


def drop_differential_1945(word: str, is_word: Callable[[str], bool]) -> str:
    """Drop the 1911 circumflex that 1945 Base XXII no longer writes (êle -> ele,
    dêste -> deste, côr -> cor, vôo -> voo). The forms of Base XXII that keep it and the
    hiatus ee of Base XXI (lêem) stay. The circumflex goes only when the bare letters
    spell a Portuguese word (``is_word``): 1911 Base XXVIII puts it on one word of a pair
    of homographs, so a word whose bare form is no word (être, prêtres) is no 1911
    differential and stays. A pre-1911 enclitic (fêl-o) stays. One-way."""
    if _RE_PRE_1911_ENCLITIC.search(word):
        return word

    def drop(part: str) -> str:
        m = _RE_CIRCUMFLEX.fullmatch(part)
        if m is None or part in _KEPT_CIRCUMFLEX_1945 or part.endswith("êem"):
            return part
        bare = m.group(1) + {"ê": "e", "ô": "o"}[m.group(2)] + m.group(3)
        return bare if _is_portuguese(bare, m.start(2), is_word) else part

    return per_segment(word, drop)


# ----------------------------------------------- 1971/73 grave subtonic removal
def strip_subtonic_grave(word: str) -> str:
    """Remove the grave/diaeretic accent of pre-1971 subtonic vowels.

    'sòmente'->'somente', 'cafèzinho'->'cafezinho'. The crasis 'à'/'às' is preserved.
    Reversible? No — it cannot be reintroduced by rule.
    """
    return (
        word.replace("è", "e")  # è
        .replace("ì", "i")  # ì
        .replace("ò", "o")  # ò
        .replace("ù", "u")  # ù
    )


# --------------------------------------------------------- AO1990 accent drops
def drop_differential(word: str, dmap: dict) -> str:
    """Drop an AO1990 differential accent, reaching inside a hyphenated compound too
    (``busca-pólos`` -> ``busca-polos``, ``pára-choques`` -> ``para-choques``). Only the
    accented differential forms are keys, so splitting never touches an unrelated part."""
    if word in dmap:
        return dmap[word]
    if "-" in word and any(p in dmap for p in word.split("-")):
        return "-".join(dmap.get(p, p) for p in word.split("-"))
    return word


def ao1990_drop_accents(word: str) -> str:
    """Drop the AO1990-abolished accents that follow a regular pattern.

    * open diphthong éi/ói in **paroxytones** (idéia->ideia, heróico->heroico) — but
      NOT oxytones (herói, anéis, papéis, faróis) or proparoxytones (alantóideo,
      einstéinio), which keep theirs;
    * circumflex on the hiatus ôo (vôo->voo, enjôo->enjoo);
    * circumflex on the 3rd-person-plural -êem (lêem->leem, vêem->veem).

    Reversible? No — eia/oi/oo also occur in words that never had an accent (meia).
    """
    return ao1990_drop_hiatus_accent(ao1990_drop_diphthong_accent(word))


_RE_OPEN_DIPHTHONG = re.compile("([éó])i")
_RE_VOWEL_RUN = re.compile("[%s]+" % _VOWELS)
# the post-tonic endings that Base XI 1º b) reads as two syllables
_RE_RISING_END = re.compile("(?:ea|eo|ia|ie|io|oa|ua|uo)s?$")


def ao1990_drop_diphthong_accent(word: str) -> str:
    """éi/ói -> ei/oi when exactly one syllable follows in its part of the word
    (idéia->ideia, jibóias->jiboias). Oxytones (herói, rói-rói) and proparoxytones
    (alantóideo, einstéinio) keep it."""
    def drop(part: str) -> str:
        def bare(m: re.Match) -> str:
            tail = part[m.end():]
            if len(_RE_VOWEL_RUN.findall(tail)) != 1 or _RE_RISING_END.search(tail):
                return m.group(0)
            return {"é": "e", "ó": "o"}[m.group(1)] + "i"

        return _RE_OPEN_DIPHTHONG.sub(bare, part)

    return per_segment(word, drop)


def ao1990_drop_hiatus_accent(word: str) -> str:
    """ôo -> oo (vôo->voo) and 3rd-person-plural êem -> eem (lêem->leem)."""
    return word.replace("ôo", "oo").replace("êem", "eem")


# ----------------------------------------------------------- AO1990 trema
# Portuguese writes the trema only after g or q (frequência, linguiça) and on a hiatus
# (saüdade). AO1990 Base XIV 1º drops it there. Its Obs. keeps it in derivatives of
# foreign names, where ü follows another consonant: "Conserva-se, no entanto, o trema, de
# acordo com a Base I, 3º, em palavras derivadas de nomes próprios estrangeiros:
# hübneriano, de Hübner, mülleriano, de Müller". The Bases Analíticas of the Acordo of
# 1945, 2, keep it too: "mülleriano, de Müller".
_TREMA_RE = re.compile(r"(?<=[gqaeiouáàâãéêíóôõú])ü")


def ao1990_drop_trema(word: str) -> str:
    """ü -> u after g, q or a vowel; reversible via lexicon only."""
    return _TREMA_RE.sub("u", word)


# --------------------------------------------------------- AO1990 months/seasons
_MONTHS = {
    "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
    "agosto", "setembro", "outubro", "novembro", "dezembro",
}
# Seasons were lowercase in every norm (only AO1990 also lowercased the months); they
# are tracked only so a season that OPENS a sentence is still capitalised.
_SEASONS = {"primavera", "verão", "outono", "inverno"}

#: opening quotes and brackets that may stand before the first word of a sentence
_OPENERS = "«“‘\"'(["

_MONTH_RE = re.compile(
    r"\b(%s)\b" % "|".join(sorted(_MONTHS | _SEASONS, key=len, reverse=True)),
    re.IGNORECASE,
)


def recase_months(text: str, lowercase: bool) -> str:
    """Set month/season casing at the text level (so sentence position is known).

    AO1990 lowercases months mid-sentence (``lowercase=True``); the older norms
    capitalise them. Seasons stay lowercase in every norm. Toward the older norms a month
    or season opening a sentence is capitalised. Toward AO1990 it keeps the case it was
    written in: Base XIX 1º b writes months and seasons in lowercase, so the conversion
    never raises one. An opening quote or bracket does not stop a sentence opening: the
    Formulário of 1943, 49. 1.º, writes the capital "No começo do período, verso ou
    citação direta" («Janeiro chegou», disse ele). A name written in capitals throughout
    keeps them: Base XIX sets the initial letter, and such a word has no lowercase letter
    to set it against. This cannot be done per-word, because case is restored from the
    source token.
    """

    def repl(m):
        word = m.group(0)
        if word.isupper():
            return word
        low = word.lower()
        cap = low[:1].upper() + low[1:]
        prefix = text[: m.start()].rstrip().rstrip(_OPENERS).rstrip()
        if prefix == "" or prefix[-1] in ".!?:—":
            return word if lowercase else cap
        if low in _SEASONS:
            return low  # seasons are always lowercase mid-sentence
        return low if lowercase else cap

    return _MONTH_RE.sub(repl, text)


# --------------------------------------------------- AO1990 prefix joins
# euro- is not in the list. In euro-africano it is europeu reduced, the first element of a
# compound of two adjectives, and AO1990 Base XV 1 writes those with the hyphen: "Emprega-se
# o hífen nas palavras compostas por justaposição que não contêm formas de ligação e cujos
# elementos, de natureza nominal, adjetival, numeral ou verbal, constituem uma unidade
# sintagmática e semântica e mantêm acento próprio, podendo dar-se o caso de o primeiro
# elemento estar reduzido: ano-luz, arcebispo-bispo, arco-íris, decreto-lei, és-sueste,
# médico-cirurgião, rainha-cláudia, tenente-coronel, tio-avô, turma-piloto; alcaide-mor,
# amor-perfeito, guarda-noturno, mato-grossense, norte-americano, porto-alegrense,
# sul-africano; afro-asiático, afro-luso-brasileiro, azul-escuro, luso-brasileiro,
# primeiro-ministro, primeiro-sargento, primo-infeção, segunda-feira; conta-gotas,
# finca-pé, guarda-chuva." The ABL VOLP and the VOP write euro-africano, euro-americano,
# euro-árabe, euro-asiático, euro-atlântico and euro-siberiano.
_RS_PREFIXES = {
    "ante", "anti", "arqui", "auto", "co", "contra", "eletro", "electro", "extra",
    "hidro", "infra", "intra", "macro", "micro", "mini", "multi", "neo",
    "pluri", "proto", "pseudo", "retro", "semi", "sobre", "supra", "ultra",
    "geo", "tele", "agro", "aero", "foto", "psico", "socio",
}


# The prefixes of _RS_PREFIXES that the 1943 Formulário, 46 5.º, does not list. 46 3.º
# Observação keeps euro- hyphenated (euro-africano), and the Pequeno Vocabulário of 1943
# writes co- with the hyphen (co-administrador, co-arrendador, co-diretor).
_UNLISTED_1943 = _RS_PREFIXES - {
    "auto", "contra", "extra", "infra", "intra", "neo", "proto", "pseudo", "semi", "ultra",
    "ante", "anti", "arqui", "sobre", "supra", "euro", "co",
}


def br_1943_prefix_join(word: str) -> str:
    """Join a prefix that the 1943 Formulário does not list to a second element that
    starts with r or s, and double the consonant (micro-sistema -> microssistema).

    The Formulário Ortográfico of 1943 (Academia Brasileira de Letras), 45: "Só se ligam
    por hífen os elementos das palavras compostas em que se mantém a noção da composição,
    isto é, os elementos das palavras compostas que mantêm a sua independência fonética,
    conservando cada um a sua própria acentuação, porém formando o conjunto perfeita
    unidade de sentido." 46 lists the cases of the hyphen, and its 5.º names the prefixes:
    auto, contra, extra, infra, intra, neo, proto, pseudo, semi and ultra (a), ante, anti,
    arqui and sôbre (b), supra (c), and super, ab, ad, ob, sob, sub, pan, mal, bem, sem,
    sota, soto, vice, vizo, ex, pós, pré and pró (d to i). 22: "Duplicam-se
    o r e o s todas as vezes que a um elemento de composição terminado em vogal se segue,
    sem interposição do hífen, palavra começada por uma daquelas letras: albirrosado,
    arritmia, altíssono, derrogar, prerrogativa, pressentir, ressentimento, sacrossanto,
    etc." The Pequeno Vocabulário of 1943 writes microssismo, microrradiógrafo,
    hidrorragia, macrorrizo, multissecular, plurissecular, geossinclinal, telessismógrafo
    and fotossíntese. Before a vowel or h the word stays as written.
    """
    pre, _, base = word.partition("-")
    if pre not in _UNLISTED_1943 or "-" in base or deaccent(base[:1]) not in ("r", "s"):
        return word
    return ao1990_hyphen_rs(word)


def ao1990_hyphen_rs(word: str, co_drops_h: bool = False) -> str:
    """Join a prefix that ends in a vowel to the second element where AO1990 Base XVI
    writes no hyphen. Restricted to a known prefix list so genuine noun+noun compounds
    (guarda-sol) are untouched.

    - Base XVI 2º a: before r or s the hyphen goes and the consonant doubles
      ('anti-religioso'->'antirreligioso', 'co-seno'->'cosseno'). Portuguese never
      writes rr or ss before a consonant, so it doubles only before a vowel
      ('anti-spam'->'antispam').
    - Base XVI 2º b: before a different vowel the hyphen goes ('auto-estrada'->
      'autoestrada'). Before the same vowel it stays (1º b: 'micro-onda').
    - Base XVI 1º b Obs.: "Nas formações com o prefixo co-, este aglutina-se em geral
      com o segundo elemento mesmo quando iniciado por o: coobrigação, coocupante,
      coordenar, cooperação, cooperar, etc." So co- joins before o too.
    - Base XVI 1: "só se emprega o hífen nos seguintes casos", so co- joins before a
      consonant ('co-fatores'->'cofatores'). The other prefixes keep the hyphen there.
    - Base XVI 1º a keeps the hyphen before h ('co-herdeiro'). With ``co_drops_h`` co-
      joins there too and the h goes ('co-herdeiro'->'coerdeiro'), as the ABL VOLP writes.

    A loanword keeps its hyphen ('co-working'), as the VOLP writes it, and so does a
    second element that does not start with a letter ('co-1').
    """
    if "-" not in word:
        return word
    parts = word.split("-")
    if len(parts) != 2:
        return word
    pre, base = parts
    if pre not in _RS_PREFIXES or not base[:1].isalpha() or is_foreign_spelling(word):
        return word
    first = deaccent(base[0])
    if first in ("r", "s"):
        doubled = base[0] if base[1:2] and base[1] in _VOWELS else ""
        return pre + doubled + base
    if first in "aeiou":
        return pre + base if pre == "co" or first != pre[-1] else word
    if pre == "co":
        if first == "h":
            return pre + base[1:] if co_drops_h else word
        return pre + base
    return word
