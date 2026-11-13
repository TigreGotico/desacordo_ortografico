"""Deterministic, regular orthographic transforms (the regex-able rules).

These are the transforms that do *not* need a lexicon: Greek-digraph simplification
(1911), the open/closed nasal-vowel alternation (PT<->BR), the AO1990 accent drops,
trema abolition, month lowercasing and prefix+r/s doubling.

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
"""
from __future__ import annotations

import re
import unicodedata
from typing import Callable, List, Mapping, Optional, Sequence, Tuple

from .lexicon import deaccent

# letters that count as part of a word (ASCII + Latin-1 accented range)
_WORD_RE = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[-'’][0-9A-Za-zÀ-ɏ]+)*")
_VOWELS = "aeiouáàâãéêíóôõúü"
# the joints of a compound word: hyphen and apostrophes
_SEGMENT_SEP = re.compile(r"[-'’]")


# ----------------------------------------------------------------- tokenising
def apply_to_words(text: str, fn: Callable[[str], str]) -> str:
    """Apply ``fn`` to each word in ``text``, preserving case and punctuation.

    ``fn`` receives a lowercase word and returns a lowercase word; the original
    capitalisation pattern (UPPER / Title / lower) is re-applied to the result, per
    hyphen or apostrophe segment (see :func:`_match_case`). A word with a capital
    inside a segment and not in capitals throughout (pH, kW, McDonald, TVs) is a symbol
    or a name, not a lowercase word, and none of the three patterns can restore it: it
    is returned as written.
    """

    def repl(match: "re.Match[str]") -> str:
        word = match.group(0)
        if not word.isupper() and any(s[1:] != s[1:].lower() for s in _SEGMENT_SEP.split(word)):
            return word
        out = fn(word.lower())
        return _match_case(word, out)

    return _WORD_RE.sub(repl, text)


def lookup_with_plural(word: str, table: Mapping[str, str]) -> Optional[str]:
    """``table[word]``, or the plural of the table form when ``word`` is the regular
    plural of a table word (aspetos from aspeto, receções from receção); else ``None``."""
    if word in table:
        return table[word]
    if word.endswith("ões") and word[:-3] + "ão" in table and table[word[:-3] + "ão"].endswith("ão"):
        return table[word[:-3] + "ão"][:-2] + "ões"
    if word.endswith("s") and word[:-1] in table and table[word[:-1]][-1:] in "aeo":
        return table[word[:-1]] + "s"
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
def reform_1911_digraphs(word: str) -> str:
    """ph->f, th->t, rh->r, y->i. Reversible? No — the inverse is ambiguous."""
    word = word.replace("ph", "f").replace("th", "t").replace("rh", "r")
    word = word.replace("y", "i")
    return word


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


_CP_DROP = [("cç", "ç"), ("ct", "t"), ("pç", "ç"), ("pt", "t")]


def drop_silent_cp(word: str, keep: set, wordset: set) -> str:
    """Drop a silent c/p from a -ct-/-pt-/-cç-/-pç- cluster (AO1990, European).

    A rule fallback for inflected forms the Base IV lexicon does not list
    (desactiva->desativa, detectou->detetou). Guarded twice so it never mangles a
    pronounced cluster: the word must not be in ``keep`` (Base IV keep + PT duals such
    as facto/contacto), and the de-consonanted form must be an attested word. One-way.
    """
    if word in keep:
        return word
    for pat, rep in _CP_DROP:
        if pat in word:
            cand = word.replace(pat, rep)
            if cand != word and cand in wordset:
                return cand
    return word


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
# city names written without an accent whose letters spell an accented common word
# (Coimbra, coimbrã; Roma, romã)
_UNACCENTED_NAMES = frozenset({"coimbra", "roma"})
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
) -> str:
    """Re-supply the graphic accent 1911 introduced (fosforo -> fósforo).

    A word that carries no accent takes the accented form from ``restore``. It takes it
    from ``nominal`` when the word before it introduces a noun phrase in ``variety``
    ("pt" or "br"): a sua historia -> a sua história. When the word before it is a clitic
    pronoun, the form is a verb and stays. When the word before it decides neither, a
    NOUN or ADJ tag gives the accent. It
    takes it from ``singular`` after a singular determiner (o pais -> o país). ``tags``
    holds one tag or ``None`` per word of ``text``. Case-preserving.
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
        accented = any(unicodedata.combining(c) for c in unicodedata.normalize("NFD", low))
        # a capital inside a segment marks a symbol or a name (McDonald, pH)
        symbol = not word.isupper() and any(s[1:] != s[1:].lower() for s in _SEGMENT_SEP.split(word))
        name = word[:1].isupper() and low in _UNACCENTED_NAMES
        form = None
        if not accented and not symbol and not name:
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
      NOT oxytones (herói, anéis, papéis, faróis keep theirs). A word is paroxytone
      (or longer) iff another vowel follows the diphthong, hence the lookahead;
    * circumflex on the hiatus ôo (vôo->voo, enjôo->enjoo);
    * circumflex on the 3rd-person-plural -êem (lêem->leem, vêem->veem).

    Reversible? No — eia/oi/oo also occur in words that never had an accent (meia).
    """
    return ao1990_drop_hiatus_accent(ao1990_drop_diphthong_accent(word))


_FOLLOWS_VOWEL = "(?=[^%s]*[%s])" % (_VOWELS, _VOWELS)


def ao1990_drop_diphthong_accent(word: str) -> str:
    """éi/ói -> ei/oi in paroxytones (idéia->ideia); oxytones keep it (herói)."""
    word = re.sub("éi%s" % _FOLLOWS_VOWEL, "ei", word)
    return re.sub("ói%s" % _FOLLOWS_VOWEL, "oi", word)


def ao1990_drop_hiatus_accent(word: str) -> str:
    """ôo -> oo (vôo->voo) and 3rd-person-plural êem -> eem (lêem->leem)."""
    return word.replace("ôo", "oo").replace("êem", "eem")


# ----------------------------------------------------------- AO1990 trema
def ao1990_drop_trema(word: str) -> str:
    """ü -> u (frequência, linguiça). Brazil-only effect; reversible via lexicon only."""
    return word.replace("ü", "u")


# --------------------------------------------------------- AO1990 months/seasons
_MONTHS = {
    "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
    "agosto", "setembro", "outubro", "novembro", "dezembro",
}
# Seasons were lowercase in every norm (only AO1990 also lowercased the months); they
# are tracked only so a season that OPENS a sentence is still capitalised.
_SEASONS = {"primavera", "verão", "outono", "inverno"}

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
    never raises one. A name written in capitals throughout keeps them: Base XIX sets the
    initial letter, and such a word has no lowercase letter to set it against. This cannot
    be done per-word, because case is restored from the source token.
    """

    def repl(m):
        word = m.group(0)
        if word.isupper():
            return word
        low = word.lower()
        cap = low[:1].upper() + low[1:]
        prefix = text[: m.start()].rstrip()
        if prefix == "" or prefix[-1] in ".!?:—":
            return word if lowercase else cap
        if low in _SEASONS:
            return low  # seasons are always lowercase mid-sentence
        return low if lowercase else cap

    return _MONTH_RE.sub(repl, text)


# --------------------------------------------------- AO1990 prefix + r/s doubling
_RS_PREFIXES = {
    "ante", "anti", "arqui", "auto", "contra", "eletro", "electro", "extra",
    "hidro", "infra", "intra", "macro", "micro", "mini", "multi", "neo",
    "pluri", "proto", "pseudo", "retro", "semi", "sobre", "supra", "ultra",
    "geo", "tele", "agro", "aero", "euro", "foto", "psico", "socio",
}


def ao1990_hyphen_rs(word: str) -> str:
    """prefix-ending-in-vowel + r/s base -> drop hyphen, double the r/s.

    'anti-religioso'->'antirreligioso', 'auto-retrato'->'autorretrato',
    'contra-senha'->'contrassenha'. Restricted to a known prefix list so genuine
    noun+noun compounds (guarda-sol) are untouched. The hyphen goes in every case,
    but the r/s doubles only before a vowel: Portuguese never writes rr or ss before
    a consonant ('anti-spam'->'antispam').
    """
    if "-" not in word:
        return word
    parts = word.split("-")
    if len(parts) != 2:
        return word
    pre, base = parts
    if pre in _RS_PREFIXES and base[:1] in ("r", "s") and pre[-1:] in _VOWELS:
        doubled = base[0] if base[1:2] and base[1] in _VOWELS else ""
        return pre + doubled + base
    return word
