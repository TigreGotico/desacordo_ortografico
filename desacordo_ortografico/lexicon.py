"""Curated exception lexicons + a thin, defensive wrapper over :mod:`tugalex`.

The deterministic rules in :mod:`desacordo_ortografico.rules` cover the regular,
reversible transforms. Everything that is *irreducibly lexical* lives here:

* AO1990 **Base IV** classification (keep / drop / dual) — see ``data/base_iv.json``;
* the differential-accent and lexicalized-hyphen exception lists;
* the PT<->BR divergence pairs that stay valid under AO1990;
* the 1911 irregulars (geminates, ch=/k/, silent consonants);
* the bulk AO1990 word maps, reused from ``tugalex`` (Portal da Lingua Portuguesa
  data) instead of being duplicated here.

``tugalex`` is a hard dependency, but every access to it is defensive: if it (or its
data) is unavailable the lexical AO1990 maps simply fall back to empty and the
deterministic rule engine still works on its own.

The 1911 accent restore keeps a bare form as written when a regular inflection makes
it a word (:func:`_inflection_kinds`). The verb forms follow the Dicionário Priberam
conjugation tables: falar for the -ar present (fala, falas, falamos, falam), the
-ar subjunctive (fale, fales, falemos, falem) and the conditional (falaria); ler for the
conditional of -er verbs (leria); correr for the -eu preterite and the -e present
(correu, corre); servir for the -ia imperfect (servia); dizer for disse. The nominal
forms follow Cunha & Cintra, *Nova Gramática do Português Contemporâneo*, 7.ª ed.,
Lexikon 2017, cap. 8 "Substantivo" (pp. 191-218) and cap. 10 "Adjetivo": the plural
adds -s after a vowel (pai, pais) and -es after r, z and s (mar, mares), and a word
in -o makes its feminine in -a (tanto, tanta; antigo, antigas).
"""
from __future__ import annotations

import json
import os
import unicodedata
from functools import cached_property
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def deaccent(word: str) -> str:
    """Strip graphic accents but keep ç: 'fósforo' -> 'fosforo'; 'maçã' -> 'maça'."""
    # keep the combining cedilla (U+0327); drop every other combining mark
    out = "".join(
        c for c in unicodedata.normalize("NFD", word)
        if not unicodedata.combining(c) or c == "\u0327"
    )
    return unicodedata.normalize("NFC", out)


def _letters(word: str) -> str:
    """Drop every diacritic: 'agüentar' -> 'aguentar', 'ação' -> 'acao'."""
    return "".join(c for c in unicodedata.normalize("NFD", word) if not unicodedata.combining(c))


#: The form without the consonant of these pt-PT dual cells is also a word of its own,
#: so it never gains the consonant: contrato (a contract) beside contracto (contracted),
#: retrato (a portrait) beside retracto (a retraction).
_DUAL_HOMOGRAPHS = frozenset({"contrato", "retrato"})


#: Irregular verb forms the word list lacks, which no inflection rule derives.
#: dizer: "ele disse" (Dicionário Priberam, conjugação de dizer, pretérito perfeito).
_IRREGULAR_FORMS = frozenset({"disse"})


def _inflection_kinds(word: str, words: Set[str]) -> FrozenSet[str]:
    """Return the kinds of regular inflection that make ``word`` a form of ``words``.

    The word list holds lemmas more than inflections, so an inflected form can look
    unattested. ``"verb"``: an irregular form, the -eu/-ou/-iu preterite (correr ->
    correu), the -ia imperfect and the -e present of -er/-ir verbs (servir -> servia,
    correr -> corre), the -a/-as/-amos/-am present and the -e/-es/-emos/-em subjunctive of
    -ar verbs (historiar -> historia, parar -> paramos), and the conditional, a stem + -ar/-er/-ir + ia
    (ler -> leria; the noun ar does not count, so aria is no verb form).
    ``"plural"``: a vowel + s plural (pai -> pais). ``"nominal"``: the -es plural
    after r, z or s (mar -> mares), the feminine plural (antigo -> antigas) and the
    feminine singular (tanto -> tanta). The sources are in the module docstring.
    """
    kinds = set()
    if word in _IRREGULAR_FORMS:
        kinds.add("verb")
    for ending, infinitive in (("eu", "er"), ("ou", "ar"), ("iu", "ir")):
        if word.endswith(ending) and word[:-2] + infinitive in words:
            kinds.add("verb")
    if word.endswith("ia") and (word[:-2] + "er" in words or word[:-2] + "ir" in words):
        kinds.add("verb")
    if word.endswith("e") and (word[:-1] + "er" in words or word[:-1] + "ir" in words):
        kinds.add("verb")
    for ending in ("a", "as", "amos", "am", "e", "es", "emos", "em"):
        if word.endswith(ending) and word[:-len(ending)] + "ar" in words:
            kinds.add("verb")
    if word.endswith(("aria", "eria", "iria")) and len(word) > 4 and word[:-2] in words:
        kinds.add("verb")
    if word.endswith("s") and word[-2:-1] in ("a", "e", "i", "o", "u") and word[:-1] in words:
        kinds.add("plural")
    if word.endswith("es") and word[-3:-2] in ("r", "z", "s") and word[:-2] in words:
        kinds.add("nominal")
    if word.endswith("as") and word[:-2] + "o" in words:
        kinds.add("nominal")
    if word.endswith("a") and word[:-1] + "o" in words:
        kinds.add("nominal")
    return frozenset(kinds)


#: The vowels after which the plural adds -s (cap. 8, see the module docstring).
_PLURAL_VOWELS = frozenset("aeiou")
#: The grave, the acute and the circumflex, the three accents of cap. 4 p. 78. An
#: accent before a final -ão marks a paroxytone: "Se é átona a sílaba onde figura o
#: til, acentua-se graficamente a predominante: acórdão, bênção, órfã" (p. 86).
_ACCENTS = frozenset("\u0300\u0301\u0302")


#: The classes of an AO1990 word-map row, see :func:`ao_row_class`.
AO_ROW_CLASSES = ("consonant", "diacritic", "trema", "join", "locution")


def ao_row_class(old: str, new: str) -> str:
    """Classify an AO1990 old -> new row by what it changes.

    ``locution``: the new form has a space (Base XV, acha-de-armas -> acha de armas);
    ``join``: a hyphen goes and the parts fuse (auto-retrato -> autorretrato);
    ``trema``: only diacritics change and the ü goes (lingüiça -> linguiça);
    ``diacritic``: only other diacritics change (idéia -> ideia, pêlo -> pelo);
    ``consonant``: the letters change (acção -> ação).
    """
    if " " in new:
        return "locution"
    if old.count("-") != new.count("-"):
        return "join"
    if deaccent(old) == deaccent(new):
        return "trema" if "ü" in old and "ü" not in new else "diacritic"
    return "consonant"


def _load(name: str) -> dict:
    with open(os.path.join(_DATA_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _strip_meta(d: dict) -> dict:
    """Drop ``_underscored`` documentation keys from a loaded JSON object."""
    return {k: v for k, v in d.items() if not k.startswith("_")}


class Lexicon:
    """Loads the curated data files and exposes ready-to-use lookup maps."""

    def __init__(self) -> None:
        self._tuga = None
        self._tuga_tried = False

    # ------------------------------------------------------- raw data files
    @cached_property
    def _base_iv(self) -> dict:
        return _load("base_iv.json")

    @cached_property
    def _differential(self) -> dict:
        return _load("differential_accents.json")

    @cached_property
    def _hyphens(self) -> dict:
        return _load("lexicalized_hyphens.json")

    @cached_property
    def _divergences(self) -> dict:
        return _load("ptbr_divergences.json")

    @cached_property
    def _reform1911(self) -> dict:
        return _load("reform_1911_irregular.json")

    @cached_property
    def _accent_71_73(self) -> dict:
        return _load("accent_reform_1971_73.json")

    @cached_property
    def sister_markers(self) -> dict:
        return _load("sister_markers.json").get("languages", {})

    # ------------------------------------------------------------ tugalex
    @property
    def tuga(self):
        """The shared :class:`tugalex.TugaLexicon`, or ``None`` if unavailable."""
        if not self._tuga_tried:
            self._tuga_tried = True
            try:
                from tugalex import TugaLexicon

                self._tuga = TugaLexicon()
            except Exception:  # pragma: no cover - optional at runtime
                self._tuga = None
        return self._tuga

    @cached_property
    def ao_pt_old2new(self) -> Dict[str, str]:
        return _clean_ao_map(self.tuga, "ao_pt")

    @cached_property
    def ao_br_old2new(self) -> Dict[str, str]:
        return _clean_ao_map(self.tuga, "ao_br")

    @cached_property
    def ao_pt_row_class(self) -> Dict[str, str]:
        """The :func:`ao_row_class` of each ``ao_pt_old2new`` row, keyed by old form."""
        return {old: ao_row_class(old, new) for old, new in self.ao_pt_old2new.items()}

    @cached_property
    def ao_br_row_class(self) -> Dict[str, str]:
        """The :func:`ao_row_class` of each ``ao_br_old2new`` row, keyed by old form."""
        return {old: ao_row_class(old, new) for old, new in self.ao_br_old2new.items()}

    @cached_property
    def ao_pt_new2old(self) -> Dict[str, str]:
        return self._ao_new2old(self.ao_pt_old2new)

    @cached_property
    def ao_br_new2old(self) -> Dict[str, str]:
        return self._ao_new2old(self.ao_br_old2new)

    @cached_property
    def ao_pt_dual_full(self) -> Dict[str, str]:
        """The dual cells of the pt-PT AO1990 map (Base IV 1º c): the form without the
        consonant -> the form with it, and the same for their plurals."""
        return _dual_full(self.tuga, "ao_pt", _DUAL_HOMOGRAPHS)

    @cached_property
    def ao_br_dual_full(self) -> Dict[str, str]:
        """The dual cells of the pt-BR AO1990 map, as :attr:`ao_pt_dual_full`."""
        return _dual_full(self.tuga, "ao_br")

    def _ao_new2old(self, old2new: Dict[str, str]) -> Dict[str, str]:
        """Invert an AO1990 word map. The bare form of a dropped differential accent
        is also a proclitic (para, pelo: Base IX 9.o), so only the forms in
        ``differential_restore`` get their accent back."""
        out = _invert(old2new)
        for bare in self.differential_dropped.values():
            out.pop(bare, None)
        out.update(self.differential_restore)
        return out

    @cached_property
    def wordset(self) -> Set[str]:
        """All known modern Portuguese word forms (lowercase), for rule validation.

        Sourced from the tugalex word list (Portal da Língua Portuguesa) plus the AO and
        1911 map values. Used to keep deterministic rules honest: a rule only fires if
        its output is an attested word.
        """
        words: Set[str] = set()
        words.update(self.ao_pt_old2new.values())
        words.update(self.ao_br_old2new.values())
        words.update(self.reform1911_old2new.values())
        t = self.tuga
        if t:
            for region in ("lbx", "rjx"):
                try:
                    words.update(w.lower() for w in t.get_wordlist(region))
                except Exception:  # pragma: no cover - optional/heavy
                    pass
        out = {w.lower() for w in words if w and " " not in w}
        # enrich with regular gender/number variants of the modern (consonant-dropped)
        # forms, so the silent-c/p rule generalises to inflections the source list omits
        # (coletivo -> coletiva/coletivos/coletivas, hence colectiva -> coletiva).
        sources = (set(self.base_iv_drop.values()) | set(self.ao_pt_old2new.values())
                   | set(self.ao_br_old2new.values()))
        for w in sources:
            if w.endswith("o"):
                out |= {w[:-1] + "a", w + "s", w[:-1] + "as"}
            elif w.endswith("a"):
                out |= {w[:-1] + "o", w + "s", w[:-1] + "os"}
        return out

    @cached_property
    def _known_letters(self) -> Set[str]:
        """The letters, without diacritics, of every word form the converter knows: the
        word set plus both sides of its word maps and exception lists."""
        words = set(self.wordset) | self.base_iv_keep | self.differential_kept
        for table in (self.ao_pt_old2new, self.ao_br_old2new, self.reform1911_old2new,
                      self.base_iv_drop, self.dual_pt2br, self.dual_br2pt,
                      self.differential_dropped, self.hyphen_dropped,
                      self.divergence_pt2br, self.divergence_br2pt, self.accent_71_73_old2new):
            words |= set(table) | set(table.values())
        return {_letters(w.lower()) for w in words}

    def is_known(self, word: str, verbs: bool = False) -> bool:
        """True when ``word``, diacritics aside, is a word form the converter knows.

        Diacritics aside, because the rules add or drop them (agüentar -> aguentar). The
        word list holds base forms, so a regular plural or feminine of a known word counts
        too (económica, insectos). Verb forms count only with ``verbs``: in the converter
        they would take acronyms (BES). A word in capitals that is not known is an
        acronym (IPTU).
        """
        letters = _letters(word)
        known = self._known_letters
        kinds = _inflection_kinds(letters, known)
        return letters in known or bool(kinds if verbs else kinds & {"nominal", "plural"})

    @cached_property
    def _accent_candidates(self) -> Dict[str, Tuple[str, FrozenSet[str]]]:
        """Map an unaccented form to its unique accented word and the inflection kinds
        (see :func:`_inflection_kinds`) that also make the bare form a word.

        A word with a tilde has two bare forms: one without the accents and the tilde
        (orgao, bençao) and one that keeps the tilde (orgão, benção). A bare form of under four letters, a bare form
        that is itself on the word list, and a bare form that deaccents from two
        accented words are left out. The plural
        in -s of each vowel-final candidate except an oxytone in -ão is added, unless
        its letters spell a word or deaccent from one, and it keeps the verb kind of
        its singular.
        """
        by_bare: Dict[str, Set[str]] = {}
        bare_words: Set[str] = set()
        for wl in self.wordset:
            d = deaccent(wl)
            by_bare.setdefault(d, set()).add(wl)
            # the tilde marks nasality and is no accent (cap. 4 p. 78-79), so the
            # form without the accents alone is a key too: orgão -> órgão
            nasal = unicodedata.normalize("NFC", "".join(
                c for c in unicodedata.normalize("NFD", wl) if c not in _ACCENTS))
            if nasal != d:
                by_bare.setdefault(nasal, set()).add(wl)
            if nasal == wl:
                bare_words.add(wl)
        out: Dict[str, Tuple[str, FrozenSet[str]]] = {}
        for bare, forms in by_bare.items():
            if len(bare) < 4 or bare in bare_words:
                continue
            accented = forms - {bare}
            if len(accented) == 1:
                out[bare] = (next(iter(accented)), _inflection_kinds(bare, bare_words))
        # the word list holds singulars; a vowel-final singular makes its plural in -s.
        # An oxytone in -ão follows its own rules (alemão, alemães) and is left out; a
        # paroxytone, which carries a written accent before -ão, adds -s. The -s form of
        # a present, imperfect or conditional verb form is the second person of the same
        # tense (corre, corres; servia, servias), so the plural keeps the verb reading.
        for bare, (form, kinds) in list(out.items()):
            plural = bare + "s"
            last_element = form.replace(" ", "-").rsplit("-", 1)[-1]
            stem_marks = _ACCENTS.intersection(unicodedata.normalize("NFD", last_element))
            oxytone_ao = form.endswith("ão") and not stem_marks
            if bare[-1] in _PLURAL_VOWELS and not oxytone_ao and plural not in by_bare:
                out[plural] = (form + "s", _inflection_kinds(plural, bare_words) | (kinds & {"verb"}))
        return out

    @cached_property
    def accent_restore(self) -> Dict[str, str]:
        """Map an unaccented word to its unique accented modern form.

        Used to re-supply the graphic accents that the 1911 reform introduced but the
        deterministic digraph/geminate rules cannot derive (phosphoro->fosforo->fósforo).
        A bare form that is itself a word stays as written ('para'/'pára',
        'esta'/'está'), and so does a regular inflection of a word: 'correu' is the
        preterite of 'correr', not a bare 'corréu'.
        """
        return {b: f for b, (f, kinds) in self._accent_candidates.items() if not kinds}

    @cached_property
    def accent_restore_nominal(self) -> Dict[str, str]:
        """The bare forms that only a verb inflection makes a word ('historia' of
        'historiar'). The accented form is right when the word is a noun or an adjective
        ('história')."""
        return {b: f for b, (f, kinds) in self._accent_candidates.items() if kinds == {"verb"}}

    @cached_property
    def accent_restore_singular(self) -> Dict[str, str]:
        """The bare forms that only a vowel + s plural makes a word ('pais' of 'pai').
        The accented form is right after a singular determiner ('o país')."""
        return {b: f for b, (f, kinds) in self._accent_candidates.items() if kinds == {"plural"}}

    @cached_property
    def cp_keep_pt(self) -> Set[str]:
        """Words whose c/p in a -ct-/-pt-/-cç-/-pç- cluster is pronounced in European
        Portuguese and therefore kept (Base IV 'keep' plus the PT side of the duals)."""
        return set(self.base_iv_keep) | set(self.dual_pt2br)

    # ----------------------------------------------------------- Base IV
    @cached_property
    def base_iv_keep(self) -> Set[str]:
        return {w.lower() for w in self._base_iv.get("keep", [])}

    @cached_property
    def base_iv_drop(self) -> Dict[str, str]:
        return {k.lower(): v.lower() for k, v in self._base_iv.get("drop", {}).items()}

    @cached_property
    def base_iv_drop_reverse(self) -> Dict[str, str]:
        return _invert(self.base_iv_drop)

    @cached_property
    def base_iv_dual(self) -> List[Dict[str, str]]:
        return self._base_iv.get("dual", [])

    @cached_property
    def dual_pt2br(self) -> Dict[str, str]:
        return {d["pt"].lower(): d["br"].lower() for d in self.base_iv_dual}

    @cached_property
    def dual_br2pt(self) -> Dict[str, str]:
        return {d["br"].lower(): d["pt"].lower() for d in self.base_iv_dual}

    # ------------------------------------------------- differential accents
    @cached_property
    def differential_dropped(self) -> Dict[str, str]:
        return {k.lower(): v.lower() for k, v in self._differential.get("dropped", {}).items()}

    @cached_property
    def differential_restore(self) -> Dict[str, str]:
        return {k.lower(): v.lower() for k, v in self._differential.get("restore", {}).items()}

    @cached_property
    def differential_kept(self) -> Set[str]:
        return {w.lower() for w in self._differential.get("kept", [])}

    # ------------------------------------------------- lexicalized hyphens
    @cached_property
    def hyphen_dropped(self) -> Dict[str, str]:
        return {k.lower(): v.lower() for k, v in self._hyphens.get("dropped", {}).items()}

    @cached_property
    def hyphen_dropped_reverse(self) -> Dict[str, str]:
        return _invert(self.hyphen_dropped)

    # ----------------------------------------------------- PT<->BR divergence
    @cached_property
    def divergence_pt2br(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for group in ("nasal_vowel", "other"):
            for d in self._divergences.get(group, []):
                out[d["pt"].lower()] = d["br"].lower()
        out.update(self.dual_pt2br)
        return out

    @cached_property
    def divergence_br2pt(self) -> Dict[str, str]:
        return _invert(self.divergence_pt2br)

    # ------------------------------------------------------- 1911 irregulars
    @cached_property
    def reform1911_old2new(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for group, entries in self._reform1911.items():
            if group.startswith("_") or not isinstance(entries, dict):
                continue
            for k, v in entries.items():
                if k.startswith("_") or not isinstance(v, str):
                    continue
                out[k.lower()] = v.lower()
        return out

    @cached_property
    def reform1911_new2old(self) -> Dict[str, str]:
        return _invert(self.reform1911_old2new)

    # --------------------------------------------------- 1971/73 differential
    @cached_property
    def accent_71_73_old2new(self) -> Dict[str, str]:
        return {k.lower(): v.lower() for k, v in self._accent_71_73.get("differential", {}).items()}

    @cached_property
    def accent_71_73_new2old(self) -> Dict[str, str]:
        return _invert(self.accent_71_73_old2new)


def _clean_ao_map(tuga, attr: str) -> Dict[str, str]:
    """Lowercase a tugalex AO map and drop its stray CSV-header entry."""
    if not tuga:
        return {}
    raw = getattr(tuga, attr, {}) or {}
    out: Dict[str, str] = {}
    for k, v in raw.items():
        if not v:
            continue
        kl, vl = k.lower().strip(), v[0].lower().strip()
        if kl == "old_form" or vl == "new_form" or not kl:
            continue  # tugalex includes the CSV header as a bogus row
        if kl == vl:
            continue  # capitalisation-only change (Janeiro->janeiro); after
            # casefolding it is a no-op that would otherwise pollute the
            # "old form" set and mislabel modern words as pre-AO1990
        out[kl] = vl
    return out


def _dual_full(tuga, attr: str, homographs: FrozenSet[str] = frozenset()) -> Dict[str, str]:
    """The form without the consonant -> the form with it, for each dual cell (a row
    with two AO1990 forms) of a tugalex AO map, and for the regular plurals of both."""
    out: Dict[str, str] = {}
    for forms in (getattr(tuga, attr, None) or {}).values():
        cell = {f.lower().strip() for f in forms if f and f.strip()}
        if len(cell) != 2:
            continue
        bare, full = sorted(cell, key=len)
        if bare in homographs:
            continue
        out[bare] = full
        plurals = _plural(bare), _plural(full)
        if None not in plurals:
            out[plurals[0]] = plurals[1]
    return out


def _plural(word: str) -> Optional[str]:
    """The plural of a dual cell form, for the endings the cells of the tugalex AO1990
    maps have: a word in -a, -e or -o takes -s, and -or and -z take -es; carácter and
    caráter make caracteres and carateres (Base IV 1º c names that pair), and the
    adjectives dactilar and datilar take -es (Aulete, datilar: "adj. || dactilar"); -ção makes
    -ções; -al makes -ais; -vel and the unstressed -il of táctil make -eis (Priberam,
    táctil: "Plural: táteis. Plural: tácteis"). ``None`` for any other form: the
    verbs and the adverbs in -mente."""
    if word in ("carácter", "caráter"):
        return deaccent(word) + "es"
    if word in ("dactilar", "datilar"):
        return word + "es"
    if word.endswith("ção"):
        return word[:-3] + "ções"
    if word.endswith(("a", "e", "o")) and not word.endswith(("ão", "mente")):
        return word + "s"
    if word.endswith(("or", "z")):
        return word + "es"
    if word.endswith("al"):
        return word[:-2] + "ais"
    if word.endswith(("vel", "til")):
        return word[:-2] + "eis"
    return None


def _invert(mapping: Dict[str, str]) -> Dict[str, str]:
    """Invert a 1:1-ish map; on collision the first key seen wins (stable)."""
    out: Dict[str, str] = {}
    for k, v in mapping.items():
        out.setdefault(v, k)
    return out


# a process-wide shared instance (the data files are read-only)
_SHARED: Optional[Lexicon] = None


def get_lexicon() -> Lexicon:
    global _SHARED
    if _SHARED is None:
        _SHARED = Lexicon()
    return _SHARED
