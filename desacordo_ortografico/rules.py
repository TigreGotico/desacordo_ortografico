"""Deterministic, regular orthographic transforms (the regex-able rules).

These are the transforms that do *not* need a lexicon: Greek-digraph simplification
(1911), the open/closed nasal-vowel alternation (PT<->BR), the AO1990 accent drops,
trema abolition, month lowercasing and prefix+r/s doubling.

Each function takes and returns a **lowercase** word; case restoration is handled by
:func:`apply_to_words`, which also tokenises the text. Functions are grouped by the
reform that introduced them and are documented as *reversible* (a clean inverse exists)
or *one-way* (the inverse is ambiguous and must be resolved by a lexicon upstream).
"""
from __future__ import annotations

import re
import unicodedata
from typing import Callable, List

# letters that count as part of a word (ASCII + Latin-1 accented range)
_WORD_RE = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[-'’][0-9A-Za-zÀ-ɏ]+)*")
_VOWELS = "aeiouáàâãéêíóôõúü"


# ----------------------------------------------------------------- tokenising
def apply_to_words(text: str, fn: Callable[[str], str]) -> str:
    """Apply ``fn`` to each word in ``text``, preserving case and punctuation.

    ``fn`` receives a lowercase word and returns a lowercase word; the original
    capitalisation pattern (UPPER / Title / lower) is re-applied to the result.
    """

    def repl(match: "re.Match[str]") -> str:
        word = match.group(0)
        out = fn(word.lower())
        return _match_case(word, out)

    return _WORD_RE.sub(repl, text)


def words(text: str) -> List[str]:
    """Return the list of word tokens in ``text`` (original case)."""
    return _WORD_RE.findall(text)


def _match_case(original: str, transformed: str) -> str:
    if original.isupper() and len(original) > 1:
        return transformed.upper()
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


def reform_1911_geminates(word: str) -> str:
    """Reduce a doubled consonant to a single one, the way 1911 did.

    Etymological geminates (anno, commando, collectiva, sufficiente) collapse, but
    the etymological ``rr``/``ss`` survive in modern spelling (carro, passo) and are
    deliberately excluded from the character class. Applied as a rule fallback so
    inflections the 1911 lexicon does not list are handled too. One-way.
    """
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


def restore_accent(word: str, accent_map) -> str:
    """Re-supply the graphic accent 1911 introduced (fosforo -> fósforo).

    Only fires on a word that currently carries no accent and whose bare form maps to
    a unique accented modern word (see ``Lexicon.accent_restore``). Case-preserving.
    """
    if not accent_map:
        return word
    low = word.lower()
    if any(unicodedata.combining(c) for c in unicodedata.normalize("NFD", low)):
        return word  # already accented
    return accent_map.get(low, word)


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
def ao1990_drop_accents(word: str) -> str:
    """Drop the AO1990-abolished accents that follow a regular pattern.

    * open diphthong éi/ói in **paroxytones** (idéia->ideia, heróico->heroico) — but
      NOT oxytones (herói, anéis, papéis, faróis keep theirs). A word is paroxytone
      (or longer) iff another vowel follows the diphthong, hence the lookahead;
    * circumflex on the hiatus ôo (vôo->voo, enjôo->enjoo);
    * circumflex on the 3rd-person-plural -êem (lêem->leem, vêem->veem).

    Reversible? No — eia/oi/oo also occur in words that never had an accent (meia).
    """
    follows_vowel = "(?=[^%s]*[%s])" % (_VOWELS, _VOWELS)
    word = re.sub("éi%s" % follows_vowel, "ei", word)  # éi -> ei (paroxytone only)
    word = re.sub("ói%s" % follows_vowel, "oi", word)  # ói -> oi (paroxytone only)
    word = word.replace("ôo", "oo")  # ôo -> oo
    word = word.replace("êem", "eem")  # êem -> eem
    return word


# ----------------------------------------------------------- AO1990 trema
def ao1990_drop_trema(word: str) -> str:
    """ü -> u (frequência, linguiça). Brazil-only effect; reversible via lexicon only."""
    return word.replace("ü", "u")


# --------------------------------------------------------- AO1990 months/seasons
_MONTHS = {
    "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
    "agosto", "setembro", "outubro", "novembro", "dezembro",
    "primavera", "verão", "outono", "inverno",
}


_MONTH_RE = re.compile(r"\b(%s)\b" % "|".join(sorted(_MONTHS, key=len, reverse=True)),
                       re.IGNORECASE)


def recase_months(text: str, lowercase: bool) -> str:
    """Set month/season casing at the text level (so sentence position is known).

    AO1990 lowercases months mid-sentence (``lowercase=True``); the older norms
    capitalise them. A month that opens a sentence stays capitalised in every norm.
    This cannot be done per-word, because case is restored from the source token.
    """

    def repl(m):
        word = m.group(0)
        low = word.lower()
        cap = low[:1].upper() + low[1:]
        prefix = text[: m.start()].rstrip()
        sentence_initial = prefix == "" or prefix[-1] in ".!?:—"
        if sentence_initial:
            return cap
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
    noun+noun compounds (guarda-sol) are untouched.
    """
    if "-" not in word:
        return word
    parts = word.split("-")
    if len(parts) != 2:
        return word
    pre, base = parts
    if pre in _RS_PREFIXES and base[:1] in ("r", "s") and pre[-1:] in _VOWELS:
        return pre + base[0] + base
    return word
