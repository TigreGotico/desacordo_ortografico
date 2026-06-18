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
"""
from __future__ import annotations

import json
import os
import unicodedata
from functools import cached_property
from typing import Dict, List, Optional, Set

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
    def ao_pt_new2old(self) -> Dict[str, str]:
        return _invert(self.ao_pt_old2new)

    @cached_property
    def ao_br_new2old(self) -> Dict[str, str]:
        return _invert(self.ao_br_old2new)

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
