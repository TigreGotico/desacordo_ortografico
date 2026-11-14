"""Curated exception lexicons and the :mod:`tugalex` word maps.

The deterministic rules in :mod:`desacordo_ortografico.rules` cover the regular,
reversible transforms. Everything that is *irreducibly lexical* lives here:

* AO1990 **Base IV** classification (keep / drop / dual) — see ``data/base_iv.json``;
* the differential-accent and lexicalized-hyphen exception lists;
* the PT<->BR divergence pairs that stay valid under AO1990;
* the 1911 irregulars (geminates, ch=/k/, silent consonants);
* the bulk AO1990 word maps, reused from ``tugalex`` (Portal da Lingua Portuguesa
  data) instead of being duplicated here.

``tugalex`` is a hard dependency: a missing package or a failed read raises, so the
output never depends on what happens to be installed.

Where both forms of a word are valid in the target variety (a dual cell of that
variety's AO1990 word map, Base IV 1º c: sector and setor), the converter writes the
form with the consonant, by owner ruling. A word with one valid form in the target
variety takes that form. A European source reaches a pt-BR norm through AO1990 pt-PT;
on that route the pt-PT step keeps the first form of a dual cell and the plain c/p rule
(:attr:`Lexicon.ao_pt_first_old2new`), so a pt-PT dual reaches Brazil unchanged by the
dual rule.

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
import re
import unicodedata
from collections import defaultdict
from functools import cached_property
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from tugalex import TugaLexicon

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


#: The prefixes that double a following r or s in AO1990 (autorretrato, antissocial).
_RS_PREFIXES = frozenset({
    "ante", "anti", "arqui", "auto", "contra", "eletro", "electro", "extra",
    "hidro", "infra", "intra", "macro", "micro", "mini", "multi", "neo",
    "pluri", "proto", "pseudo", "retro", "semi", "sobre", "supra", "ultra",
    "geo", "tele", "agro", "aero", "euro", "foto", "psico", "socio",
})

#: Prefixes and leading elements after which a base keeps its own AO1990 spelling
#: (autoinfecção -> autoinfeção, codialecto -> codialeto).
_CP_PREFIXES = _RS_PREFIXES | {"co", "des", "hiper", "inter", "pós", "pré", "sub", "super"}

#: The c or p of a -cç-/-ct-/-pç-/-pt- cluster.
_CP_CLUSTER_RE = re.compile(r"[cp](?=[tç])")

#: The forms without the consonant of a pt-PT dual that are words of their own, so they
#: never gain the consonant: contrato (a contract) beside contracto (contracted), retrato
#: (a portrait) beside retracto (a retraction).
_DUAL_HOMOGRAPHS = frozenset({"contrato", "retrato"})


class Lexicon:
    """Loads the curated data files and exposes ready-to-use lookup maps."""

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
    @cached_property
    def tuga(self) -> TugaLexicon:
        """The shared :class:`tugalex.TugaLexicon`."""
        return TugaLexicon()

    @cached_property
    def ao_pt_forms(self) -> Dict[str, List[str]]:
        """The tugalex pt-PT AO1990 map: old form -> its AO1990 forms (two for a dual)."""
        return _ao_forms(self.tuga.ao_pt)

    @cached_property
    def ao_br_forms(self) -> Dict[str, List[str]]:
        return _ao_forms(self.tuga.ao_br)

    @cached_property
    def ao_pt_old2new(self) -> Dict[str, str]:
        return _old2new(self.ao_pt_forms)

    @cached_property
    def ao_pt_first_old2new(self) -> Dict[str, str]:
        """The pt-PT map with the first form of each dual cell, for a route to pt-BR."""
        return _old2new(self.ao_pt_forms, first=True)

    @cached_property
    def ao_br_old2new(self) -> Dict[str, str]:
        return _old2new(self.ao_br_forms)

    @cached_property
    def _pt_duals(self) -> Dict[str, Tuple[str, str]]:
        """The dual cells of the pt-PT map: old form -> (the AO1990 form with the
        consonant, the form without it)."""
        return {old: (max(forms, key=len), min(forms, key=len))
                for old, forms in self.ao_pt_forms.items() if len(forms) > 1}

    @cached_property
    def _br_duals(self) -> Dict[str, Tuple[str, str]]:
        """The dual cells of the pt-BR map, keyed by old form like :attr:`_pt_duals`."""
        return {old: (max(forms, key=len), min(forms, key=len))
                for old, forms in self.ao_br_forms.items() if len(forms) > 1}

    @cached_property
    def ao_br_dual_full(self) -> Dict[str, str]:
        """The form without the consonant of each pt-BR dual cell -> the form with it."""
        return {bare: full for full, bare in self._br_duals.values()}

    @cached_property
    def _word_list(self) -> Set[str]:
        """The tugalex word list (Portal da Língua Portuguesa), lowercase."""
        return {w.lower() for region in ("lbx", "rjx") for w in self.tuga.get_wordlist(region)}

    @cached_property
    def attested(self) -> Set[str]:
        """The words valid as written in pt-PT: the forms the pt-PT AO1990 map gives, and
        the words of the word list. The list holds pre-AO1990 forms too, so the old form
        of a c/p row of either AO1990 map is left out, compared without diacritics
        (microelectrônica beside microelectrónica)."""
        old = {deaccent(o) for table in (self.ao_pt_forms, self.ao_br_forms)
               for o, forms in table.items() if o not in forms and _CP_CLUSTER_RE.search(o)}
        listed = {w for w in self._word_list if deaccent(w) not in old}
        return listed | {f for forms in self.ao_pt_forms.values() for f in forms}

    def _cp_outcome_pt(self, key: str) -> Optional[str]:
        """'drop' when the pt-PT AO1990 form of map word ``key`` loses the c/p of its
        first cluster, 'keep' when the form keeps it, ``None`` for any other change."""
        match = _CP_CLUSTER_RE.search(key)
        if not match:
            return None
        form = self.ao_pt_old2new.get(key, key)
        if form == key:
            return "keep"
        if form == key[:match.start()] + key[match.start() + 1:]:
            return "drop"
        return None

    @cached_property
    def _cp_stems_pt(self) -> Dict[str, Set[str]]:
        """Stems -> the outcomes of the words that share them. A stem ends one letter
        past the c/p cluster (acto, detecta). The words are the map words and the Base IV
        keep list (apto, pacto); a map row overrides the keep list (ruptura -> rutura). A
        dual cell speaks only for itself, so contractura does not keep contractual."""
        stems: Dict[str, Set[str]] = defaultdict(set)
        words = [(key, self._cp_outcome_pt(key)) for key in self.ao_pt_forms
                 if key not in self._pt_duals]
        words += [(word, "keep") for word in self.cp_keep_pt if word not in self.ao_pt_forms]
        for word, outcome in words:
            match = _CP_CLUSTER_RE.search(word)
            if match and outcome and len(word) >= match.start() + 3:
                stems[word[:match.start() + 3]].add(outcome)
        return stems

    @cached_property
    def _pt_dual_full_forms(self) -> Set[str]:
        """The forms with the consonant of the pt-PT duals and their plurals. Cunha &
        Cintra cap. 8, "Substantivos terminados em consoante": -s after a vowel, -es after
        r and z, -al becomes -ais, and carácter makes caracteres (Observação 1.ª, the
        stress moves)."""
        out: Set[str] = set()
        for full, _bare in self._pt_duals.values():
            out.add(full)
            if full[-1:] in _PLURAL_VOWELS:
                out.add(full + "s")
            elif full[-1:] in "rz":
                out.add(deaccent(full) + "es")
            elif full.endswith("al"):
                out.add(full[:-2] + "ais")
        return out

    def cp_ao_form_pt(self, word: str) -> Optional[str]:
        """The pt-PT AO1990 form of ``word`` that the tugalex map gives its base, or
        ``None`` with no map evidence.

        The evidence, in order: the map row of the word or of its masculine singular
        (anticonceptiva and anticonceptivo, espectadores and espectador); the row of its base after a prefix
        (autoinfecção, codialecto), unless that base is a dual cell; for a word the word
        list does not attest, the evidence of its masculine singular (aptas and apto);
        then the map words that share its stem one letter past the cluster (actores and
        actor). Stem words that disagree give no evidence.
        """
        match = _CP_CLUSTER_RE.search(word)
        if not match:
            return None
        cut = match.start()
        drop = word[:cut] + word[cut + 1:]
        singular = word.removesuffix("s")
        bases = [singular, singular[:-1] + "o"] if singular.endswith("a") else [singular]
        if word.endswith("es") and word[-3:-2] in ("r", "z"):
            bases.append(word[:-2])  # Cunha & Cintra cap. 8: -es after r and z
        for base in dict.fromkeys([word] + bases):
            outcome = self._cp_outcome_pt(base) if base in self.ao_pt_forms else None
            if outcome is not None and _CP_CLUSTER_RE.search(base).start() == cut:
                return drop if outcome == "drop" else word
        for p in _CP_PREFIXES:
            base = word[len(p):]
            if (word.startswith(p) and len(p) <= cut and len(base) >= 5
                    and base in self.ao_pt_forms and base not in self._pt_duals):
                outcome = self._cp_outcome_pt(base)
                if outcome is not None and _CP_CLUSTER_RE.search(base).start() == cut - len(p):
                    return drop if outcome == "drop" else word
        if word in self.attested:
            return None
        for base in bases:
            if base == word:
                continue
            form = self.cp_ao_form_pt(base)
            if form is not None:
                return word if form == base else drop
            if base in self.attested:
                return word
        outcomes = self._cp_stems_pt.get(word[:cut + 3], set())
        if len(word) >= cut + 3 and len(outcomes) == 1:
            return drop if outcomes == {"drop"} else word
        return None

    @cached_property
    def ao_pt_row_class(self) -> Dict[str, str]:
        """The :func:`ao_row_class` of each row of both pt-PT maps, keyed by old form."""
        return {old: ao_row_class(old, new)
                for table in (self.ao_pt_first_old2new, self.ao_pt_old2new)
                for old, new in table.items()}

    @cached_property
    def ao_br_row_class(self) -> Dict[str, str]:
        """The :func:`ao_row_class` of each ``ao_br_old2new`` row, keyed by old form."""
        return {old: ao_row_class(old, new) for old, new in self.ao_br_old2new.items()}

    @cached_property
    def ao_pt_new2old(self) -> Dict[str, str]:
        """Invert the pt-PT map. The form without the consonant of a dual also goes back
        (setor -> sector), unless it is a word of its own (contrato)."""
        out = self._ao_new2old(self.ao_pt_old2new)
        for old, (_full, bare) in self._pt_duals.items():
            if bare not in _DUAL_HOMOGRAPHS:
                out.setdefault(bare, old)
        return out

    @cached_property
    def ao_br_new2old(self) -> Dict[str, str]:
        """Invert the pt-BR map. The form with the consonant of a dual that is itself a
        pre-AO1990 spelling stays (liquefacto). The form without it goes back as the
        first form of the map row (codialeto -> co-dialecto, liquefação -> liquefacção)."""
        out = self._ao_new2old(self.ao_br_old2new)
        for old, (full, _bare) in self._br_duals.items():
            if full == old:
                out.pop(full, None)
        first = self._ao_new2old(_old2new(self.ao_br_forms, first=True))
        for _full, bare in set(self._br_duals.values()):
            if bare in first:
                out.setdefault(bare, first[bare])
        return out

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
        firsts = {forms[0] for table in (self.ao_pt_forms, self.ao_br_forms)
                  for old, forms in table.items() if forms[0] != old}
        words = firsts | set(self.reform1911_old2new.values()) | self._word_list
        out = {w.lower() for w in words if w and " " not in w}
        # enrich with regular gender/number variants of the modern (consonant-dropped)
        # forms, so the silent-c/p rule generalises to inflections the source list omits
        # (coletivo -> coletiva/coletivos/coletivas, hence colectiva -> coletiva).
        for w in set(self.base_iv_drop.values()) | firsts:
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
        words |= set(self.ao_pt_forms) | set(self.ao_br_forms)
        for table in (self.ao_pt_old2new, self.ao_br_old2new, self.reform1911_old2new,
                      self.base_iv_drop, self.dual_pt2br, self.dual_br2pt,
                      self.differential_dropped, self.hyphen_dropped,
                      self.divergence_pt2br, self.divergence_br2pt, self.accent_71_73_old2new):
            words |= set(table) | set(table.values())
        return {_letters(w.lower()) for w in words}

    def is_known(self, word: str) -> bool:
        """True when ``word``, diacritics aside, is a word form the converter knows.

        Diacritics aside, because the rules add or drop them (agüentar -> aguentar). The
        word list holds base forms, so a regular plural or feminine of a known word counts
        too (económica, insectos). Verb forms do not: they would take acronyms (BES). A
        word in capitals that is not known is an acronym (IPTU).
        """
        letters = _letters(word)
        known = self._known_letters
        return letters in known or bool({"nominal", "plural"} & _inflection_kinds(letters, known))

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

    @cached_property
    def ptbr_br2pt(self) -> Dict[str, str]:
        """``divergence_br2pt`` without the pt-BR forms whose consonant pt-PT keeps by the
        dual rule (espectador, caracteres)."""
        return {br: pt for br, pt in self.divergence_br2pt.items()
                if br not in self._pt_dual_full_forms}

    @cached_property
    def ao_dual_br2pt(self) -> Dict[str, str]:
        """The dual cells, form without the consonant -> form with it, for a pt-PT target
        (setor -> sector). A pt-BR dual goes only where the pt-PT map has no row of its
        own (liquefato -> liquefacto, but codialeto stays). A word of its own stays
        (contrato)."""
        out: Dict[str, str] = {}
        for full, bare in self._pt_duals.values():
            if bare not in _DUAL_HOMOGRAPHS:
                out.setdefault(bare, full)
        pt_forms = set(self.ao_pt_forms) | {f for forms in self.ao_pt_forms.values() for f in forms}
        for full, bare in self._br_duals.values():
            if full not in pt_forms and bare not in pt_forms:
                out.setdefault(bare, full)
        return out

    @cached_property
    def ao_br_full2pt(self) -> Dict[str, str]:
        """The form with the consonant of a pt-BR dual cell -> the one form the pt-PT
        map gives it, for an AO1990 pt-PT target (liquefacção -> liquefação)."""
        return {full: self.ao_pt_old2new[full] for full, _bare in self._br_duals.values()
                if full in self.ao_pt_old2new}

    # ------------------------------------------------------- 1911 irregulars
    @cached_property
    def reform1911_old2new(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for group, entries in self._reform1911.items():
            if group.startswith("_") or group == "frequent_reading" or not isinstance(entries, dict):
                continue
            for k, v in entries.items():
                if k.startswith("_") or not isinstance(v, str):
                    continue
                out[k.lower()] = v.lower()
        return out

    @cached_property
    def reform1911_forward(self) -> Dict[str, str]:
        """``reform1911_old2new`` plus the pre-1911 forms that read as their more frequent
        word (contracto -> contrato). These go forward only: pre-1911 text writes the noun
        both ways, so a modern contrato stays."""
        group = self._reform1911["frequent_reading"]
        return {**self.reform1911_old2new,
                **{k.lower(): v.lower() for k, v in group.items() if not k.startswith("_")}}

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


def _ao_forms(raw: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Lowercase a tugalex AO map and drop its stray CSV-header entry."""
    out: Dict[str, List[str]] = {}
    for old, new in raw.items():
        old = old.lower().strip()
        forms = list(dict.fromkeys(f.lower().strip() for f in new if f.strip()))
        if old and forms and old != "old_form" and forms[0] != "new_form":
            out[old] = forms
    return out


def _invert(mapping: Dict[str, str]) -> Dict[str, str]:
    """Invert a 1:1-ish map; on collision the first key seen wins (stable)."""
    out: Dict[str, str] = {}
    for k, v in mapping.items():
        out.setdefault(v, k)
    return out


def _old2new(forms: Dict[str, List[str]], first: bool = False) -> Dict[str, str]:
    """One AO1990 form per old form. A dual cell gives the form with the consonant
    (the longer one), or with ``first`` the form the map lists first. Rows
    whose form equals the old form (a pt-PT dual, a capital-only change such as Janeiro)
    are left out: they would mark modern words as pre-AO1990."""
    out: Dict[str, str] = {}
    for old, new in forms.items():
        form = new[0] if first else max(new, key=len)
        if form != old:
            out[old] = form
    return out


# a process-wide shared instance (the data files are read-only)
_SHARED: Optional[Lexicon] = None


def get_lexicon() -> Lexicon:
    global _SHARED
    if _SHARED is None:
        _SHARED = Lexicon()
    return _SHARED
