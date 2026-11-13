"""Curated exception lexicons + a thin, defensive wrapper over :mod:`tugalex`.

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
"""
from __future__ import annotations

import json
import os
import unicodedata
from collections import defaultdict
from functools import cached_property
from typing import Dict, List, Optional, Set

from tugalex import TugaLexicon

from desacordo_ortografico import rules

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def deaccent(word: str) -> str:
    """Strip graphic accents but keep ç: 'fósforo' -> 'fosforo'; 'maçã' -> 'maça'."""
    # keep the combining cedilla (U+0327); drop every other combining mark
    out = "".join(
        c for c in unicodedata.normalize("NFD", word)
        if not unicodedata.combining(c) or c == "\u0327"
    )
    return unicodedata.normalize("NFC", out)


def _load(name: str) -> dict:
    with open(os.path.join(_DATA_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _strip_meta(d: dict) -> dict:
    """Drop ``_underscored`` documentation keys from a loaded JSON object."""
    return {k: v for k, v in d.items() if not k.startswith("_")}


# Prefixes and leading elements after which a base keeps its own AO1990 spelling
# (autoinfecção -> autoinfeção, codialecto -> codialeto).
_CP_PREFIXES = rules.RS_PREFIXES | {"co", "des", "hiper", "inter", "pós", "pré", "sub", "super"}


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
        return self._old2new(self.ao_pt_forms, "pt-PT")

    @cached_property
    def ao_br_old2new(self) -> Dict[str, str]:
        return self._old2new(self.ao_br_forms, "pt-BR")

    def _old2new(self, forms: Dict[str, List[str]], lang: str) -> Dict[str, str]:
        """One AO1990 form per old form. A dual takes the form tugalex prefers for
        ``lang`` (``TugaLexicon.modern_spelling``). Rows whose form equals the old form
        (a kept dual, a capital-only change such as Janeiro) are left out."""
        out: Dict[str, str] = {}
        for old, new in forms.items():
            form = new[0] if len(new) == 1 else self.tuga.modern_spelling(old, lang).lower()
            if form != old:
                out[old] = form
        return out

    def _cp_outcome_pt(self, key: str) -> Optional[str]:
        """'drop' when the pt-PT AO1990 form of map word ``key`` loses the c/p of its
        first cluster, 'keep' when the form keeps it, ``None`` for any other change."""
        match = rules.CP_CLUSTER_RE.search(key)
        if not match:
            return None
        form = self.tuga.modern_spelling(key, "pt-PT").lower()
        if form == key:
            return "keep"
        if form == key[:match.start()] + key[match.start() + 1:]:
            return "drop"
        return None

    @cached_property
    def _cp_stems_pt(self) -> Dict[str, Set[str]]:
        """Stems -> the outcomes of the words that share them. A stem ends one letter
        past the c/p cluster (acto, detecta) or at the cluster (apt, tect). The words are
        the map words and the Base IV keep list (apto, pacto)."""
        stems: Dict[str, Set[str]] = defaultdict(set)
        words = [(key, self._cp_outcome_pt(key)) for key in self.ao_pt_forms]
        words += [(word, "keep") for word in self.cp_keep_pt]
        for word, outcome in words:
            match = rules.CP_CLUSTER_RE.search(word)
            if match and outcome:
                for end in (match.start() + 3, match.start() + 2):
                    if len(word) >= end:
                        stems[word[:end]].add(outcome)
        return stems

    def cp_ao_form_pt(self, word: str) -> Optional[str]:
        """The pt-PT AO1990 form of ``word`` that the tugalex map gives its base, or
        ``None`` with no map evidence.

        The base is the word itself, the word after a prefix (autoinfecção, codialecto),
        or, for a word the word list lacks, the words that share its stem (actores and
        actor, efectuado and efectuar, apta and apto). The stem one letter past the
        cluster decides first; stem words that disagree give no evidence. The shorter
        stem that ends at the cluster only keeps a consonant, never drops one.
        """
        match = rules.CP_CLUSTER_RE.search(word)
        if not match:
            return None
        cut = match.start()
        drop = word[:cut] + word[cut + 1:]
        starts = [0] + [len(p) for p in _CP_PREFIXES
                        if word.startswith(p) and len(p) <= cut and len(word) - len(p) >= 5]
        for start in sorted(starts):
            base = word[start:]
            if base in self.ao_pt_forms:
                outcome = self._cp_outcome_pt(base)
                if outcome is not None and rules.CP_CLUSTER_RE.search(base).start() == cut - start:
                    return drop if outcome == "drop" else word
        if word in self.wordset:
            return None  # stems speak only for forms the word list lacks (inflections)
        outcomes = self._cp_stems_pt.get(word[:cut + 3], set())
        if len(word) >= cut + 3 and len(outcomes) == 1:
            return drop if outcomes == {"drop"} else word
        # a stem that ends at the cluster is too short to drop on (tect: tecto, tectónico)
        if self._cp_stems_pt.get(word[:cut + 2]) == {"keep"}:
            return word
        return None

    @cached_property
    def ao_pt_new2old(self) -> Dict[str, str]:
        return _invert_forms(self.ao_pt_forms)

    @cached_property
    def ao_br_new2old(self) -> Dict[str, str]:
        return _invert_forms(self.ao_br_forms)

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
        for region in ("lbx", "rjx"):
            words.update(w.lower() for w in self.tuga.get_wordlist(region))
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
    def accent_restore(self) -> Dict[str, str]:
        """Map an unaccented word to its unique accented modern form.

        Used to re-supply the graphic accents that the 1911 reform introduced but the
        deterministic digraph/geminate rules cannot derive (phosphoro->fosforo->fósforo).
        Only unambiguous entries are kept: an unaccented key is included only if exactly
        one accented word deaccents to it AND that bare form is not itself a valid word
        (so 'para'/'pára', 'esta'/'está' are never touched).
        """
        by_bare: Dict[str, Set[str]] = {}
        bare_words: Set[str] = set()
        for wl in self.wordset:
            d = deaccent(wl)
            by_bare.setdefault(d, set()).add(wl)
            if d == wl:
                bare_words.add(wl)
        out: Dict[str, str] = {}
        for bare, forms in by_bare.items():
            if len(bare) < 4 or bare in bare_words:
                continue
            accented = forms - {bare}
            if len(accented) == 1:
                out[bare] = next(iter(accented))
        return out

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


def _ao_forms(raw: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Lowercase a tugalex AO map and drop its stray CSV-header entry."""
    out: Dict[str, List[str]] = {}
    for old, new in raw.items():
        old = old.lower().strip()
        forms = [f.lower().strip() for f in new if f.strip()]
        if old and forms and old != "old_form" and forms[0] != "new_form":
            out[old] = forms
    return out


def _invert(mapping: Dict[str, str]) -> Dict[str, str]:
    """Invert a 1:1-ish map; on collision the first key seen wins (stable)."""
    out: Dict[str, str] = {}
    for k, v in mapping.items():
        out.setdefault(v, k)
    return out


def _invert_forms(forms: Dict[str, List[str]]) -> Dict[str, str]:
    """First-listed AO1990 form -> old form, kept duals included (setor -> sector). A
    second-listed form is often a word of its own (contracto: contracto, contrato), so it
    does not go back. On collision the first row wins."""
    out: Dict[str, str] = {}
    for old, new in forms.items():
        if new[0] != old:
            out.setdefault(new[0], old)
    return out


# a process-wide shared instance (the data files are read-only)
_SHARED: Optional[Lexicon] = None


def get_lexicon() -> Lexicon:
    global _SHARED
    if _SHARED is None:
        _SHARED = Lexicon()
    return _SHARED
