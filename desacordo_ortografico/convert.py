"""Convert text between Portuguese orthographic norms.

A conversion is a path through the norm graph (:mod:`desacordo_ortografico.eras`).
Each edge carries a *forward* (older->newer) and *backward* transform built from the
deterministic rules (:mod:`rules`) and the curated/`tugalex` lexicons
(:mod:`lexicon`). Where an authoritative word map exists (the AO1990 edges, via
``tugalex``) it is applied first and the rules act only as a fallback for words the
map does not cover.

Forward conversion (toward newer norms) is well defined. Backward conversion is, for
several edges, *lexical and lossy*: dropping a silent consonant or an accent throws
away information that no rule can recover. The :class:`ConversionResult` reports this
via ``lossless`` and ``warnings`` instead of silently guessing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from . import rules
from .eras import Norm, find_path
from .lexicon import Lexicon, get_lexicon

# a per-edge transform: (word, variant) -> word
WordFn = Callable[[str, Optional[str]], str]


@dataclass
class _Edge:
    """Forward/backward word transforms for one graph edge."""

    forward: WordFn
    backward: WordFn
    reversible_forward: bool = True
    reversible_backward: bool = True
    note: str = ""


@dataclass
class ConversionResult:
    """The outcome of a conversion."""

    text: str
    source: str
    target: str
    lossless: bool = True
    warnings: List[str] = field(default_factory=list)
    alternatives: Dict[str, List[str]] = field(default_factory=dict)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.text


class OrthographyConverter:
    """Stateful converter holding the shared :class:`Lexicon`."""

    def __init__(self, lexicon: Optional[Lexicon] = None) -> None:
        self.lex = lexicon or get_lexicon()
        self._edges = self._build_edges()

    # -------------------------------------------------------------- public API
    def convert(
        self,
        text: str,
        source: "str | Norm",
        target: "str | Norm",
        variant: Optional[str] = None,
    ) -> ConversionResult:
        src = Norm.parse(source)
        dst = Norm.parse(target)
        steps = find_path(src, dst)
        result = ConversionResult(text=text, source=src.id, target=dst.id)
        if not steps:
            return result

        # the variant biases dual-form selection when crossing the divergence edge
        var = variant or (dst.variant.value or src.variant.value or None)

        out = text
        for edge_name, _frm, forward in steps:
            edge = self._edges[edge_name]
            fn = edge.forward if forward else edge.backward
            reversible = edge.reversible_forward if forward else edge.reversible_backward
            out = rules.apply_to_words(out, lambda w: fn(w, var))
            if not reversible:
                result.lossless = False
                direction = "forward" if forward else "backward"
                msg = f"{edge_name} ({direction}) is lexical/lossy"
                if edge.note:
                    msg += f": {edge.note}"
                if msg not in result.warnings:
                    result.warnings.append(msg)

        result.text = out
        result.alternatives = self._collect_alternatives(text, dst)
        return result

    def permitted_spellings(self, word: str, norm: "str | Norm") -> List[str]:
        """All officially permitted spellings of ``word`` in ``norm``.

        For AO1990 this can be two forms (the PT and BR variants of a Base IV dual or a
        nasal-vowel divergence); for unambiguous words it is a single-element list.
        """
        n = Norm.parse(norm)
        low = word.lower()
        forms = [low]
        if n.era.value == "ao1990":
            lex = self.lex
            if low in lex.dual_pt2br:
                forms = [low, lex.dual_pt2br[low]]
            elif low in lex.dual_br2pt:
                forms = [lex.dual_br2pt[low], low]
            elif low in lex.divergence_pt2br:
                forms = [low, lex.divergence_pt2br[low]]
            elif low in lex.divergence_br2pt:
                forms = [lex.divergence_br2pt[low], low]
        # de-duplicate, keep order
        seen = set()
        uniq = []
        for f in forms:
            if f not in seen:
                seen.add(f)
                uniq.append(f)
        return uniq

    # ----------------------------------------------------------- alternatives
    def _collect_alternatives(self, text: str, dst: Norm) -> Dict[str, List[str]]:
        if dst.era.value != "ao1990":
            return {}
        alts: Dict[str, List[str]] = {}
        for w in rules.words(text):
            low = w.lower()
            for table in (self.lex.dual_pt2br, self.lex.dual_br2pt,
                          self.lex.divergence_pt2br, self.lex.divergence_br2pt):
                if low in table:
                    forms = self.permitted_spellings(low, dst)
                    if len(forms) > 1:
                        alts[low] = forms
                    break
        return alts

    # --------------------------------------------------------------- the edges
    def _build_edges(self) -> Dict[str, _Edge]:
        lex = self.lex

        # -- 1911 -----------------------------------------------------------
        def reform_1911_fwd(w: str, _v: Optional[str]) -> str:
            if w in lex.reform1911_old2new:
                return lex.reform1911_old2new[w]
            return rules.reform_1911_digraphs(w)

        def reform_1911_bwd(w: str, _v: Optional[str]) -> str:
            return lex.reform1911_new2old.get(w, w)

        # -- 1911 <-> 1945 (PT): orthographically near-identical --------------
        def identity(w: str, _v: Optional[str]) -> str:
            return w

        # -- 1911 <-> 1943 (BR) ----------------------------------------------
        def br_1943_fwd(w: str, _v: Optional[str]) -> str:
            w = lex.base_iv_drop.get(w, w)
            return rules.nasal_vowel_to_br(w)

        def br_1943_bwd(w: str, _v: Optional[str]) -> str:
            w = lex.base_iv_drop_reverse.get(w, w)
            return rules.nasal_vowel_to_pt(w)

        # -- 1945 <-> 1973 (PT accent reform) --------------------------------
        def accent_1973_fwd(w: str, _v: Optional[str]) -> str:
            w = lex.accent_71_73_old2new.get(w, w)
            return rules.strip_subtonic_grave(w)

        def accent_1973_bwd(w: str, _v: Optional[str]) -> str:
            return lex.accent_71_73_new2old.get(w, w)

        # -- 1943 <-> 1971 (BR accent reform; trema survives until AO1990) ----
        accent_1971_fwd = accent_1973_fwd
        accent_1971_bwd = accent_1973_bwd

        # -- pre-AO90 PT <-> AO1990 PT ---------------------------------------
        def ao_pt_fwd(w: str, _v: Optional[str]) -> str:
            if w in lex.ao_pt_old2new:
                return lex.ao_pt_old2new[w]
            w = lex.differential_dropped.get(w, w)
            w = lex.hyphen_dropped.get(w, w)
            w = lex.base_iv_drop.get(w, w)
            w = rules.ao1990_drop_trema(w)
            w = rules.ao1990_drop_accents(w)
            w = rules.ao1990_hyphen_rs(w)
            w = rules.ao1990_lowercase_month(w)
            return w

        def ao_pt_bwd(w: str, _v: Optional[str]) -> str:
            if w in lex.ao_pt_new2old:
                return lex.ao_pt_new2old[w]
            w = lex.hyphen_dropped_reverse.get(w, w)
            w = lex.base_iv_drop_reverse.get(w, w)
            w = rules.restore_capital_month(w)
            return w

        # -- pre-AO90 BR <-> AO1990 BR ---------------------------------------
        def ao_br_fwd(w: str, _v: Optional[str]) -> str:
            if w in lex.ao_br_old2new:
                return lex.ao_br_old2new[w]
            w = lex.differential_dropped.get(w, w)
            w = lex.hyphen_dropped.get(w, w)
            w = rules.ao1990_drop_trema(w)
            w = rules.ao1990_drop_accents(w)
            w = rules.ao1990_hyphen_rs(w)
            w = rules.ao1990_lowercase_month(w)
            return w

        def ao_br_bwd(w: str, _v: Optional[str]) -> str:
            if w in lex.ao_br_new2old:
                return lex.ao_br_new2old[w]
            w = lex.hyphen_dropped_reverse.get(w, w)
            w = rules.restore_capital_month(w)
            return w

        # -- AO1990 PT <-> AO1990 BR (lateral divergence) --------------------
        def ptbr_fwd(w: str, _v: Optional[str]) -> str:  # pt -> br
            if w in lex.divergence_pt2br:
                return lex.divergence_pt2br[w]
            return rules.nasal_vowel_to_br(w)

        def ptbr_bwd(w: str, _v: Optional[str]) -> str:  # br -> pt
            if w in lex.divergence_br2pt:
                return lex.divergence_br2pt[w]
            return rules.nasal_vowel_to_pt(w)

        return {
            "reform_1911": _Edge(
                reform_1911_fwd, reform_1911_bwd,
                reversible_backward=False,
                note="1911 digraph simplification (ph/th/y) cannot be reversed by rule",
            ),
            "pt_1911_to_1945": _Edge(identity, identity),
            "br_1911_to_1943": _Edge(
                br_1943_fwd, br_1943_bwd,
                reversible_backward=False,
                note="silent-consonant restoration is lexical",
            ),
            "accent_1973": _Edge(
                accent_1973_fwd, accent_1973_bwd,
                reversible_backward=False,
                note="subtonic grave accents cannot be reintroduced by rule",
            ),
            "accent_1971": _Edge(
                accent_1971_fwd, accent_1971_bwd,
                reversible_backward=False,
                note="subtonic grave accents cannot be reintroduced by rule",
            ),
            "ao1990_pt": _Edge(
                ao_pt_fwd, ao_pt_bwd,
                reversible_backward=False,
                note="dropped accents/consonants are restored from a lexicon, not a rule",
            ),
            "ao1990_br": _Edge(
                ao_br_fwd, ao_br_bwd,
                reversible_backward=False,
                note="dropped accents/trema are restored from a lexicon, not a rule",
            ),
            "ptbr_divergence": _Edge(ptbr_fwd, ptbr_bwd),
        }


# ------------------------------------------------------------- convenience API
_CONVERTER: Optional[OrthographyConverter] = None


def _converter() -> OrthographyConverter:
    global _CONVERTER
    if _CONVERTER is None:
        _CONVERTER = OrthographyConverter()
    return _CONVERTER


def convert(
    text: str,
    source: "str | Norm",
    target: "str | Norm",
    variant: Optional[str] = None,
) -> str:
    """Convert ``text`` from ``source`` to ``target`` and return the string.

    For the full result (warnings, dual-form alternatives) use
    :meth:`OrthographyConverter.convert`.
    """
    return _converter().convert(text, source, target, variant).text
