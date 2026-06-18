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
from typing import Callable, Dict, List, Optional

from . import rules
from .eras import NORMS, Era, Norm, find_path
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
        if variant is not None:
            variant = variant.lower()
            if variant not in ("pt", "br"):
                raise ValueError(f"variant must be 'pt' or 'br', got {variant!r}")
            # an explicit variant selects the European/Brazilian AO1990 sub-norm
            # (so `convert(t, src, "ao1990", variant="br")` lands on ao1990-br)
            if dst.era == Era.AO1990:
                dst = NORMS[f"ao1990-{variant}"]
        steps = find_path(src, dst)
        result = ConversionResult(text=text, source=src.id, target=dst.id)
        if not steps:
            return result

        out = text
        for edge_name, _frm, forward in steps:
            edge = self._edges[edge_name]
            fn = edge.forward if forward else edge.backward
            reversible = edge.reversible_forward if forward else edge.reversible_backward
            out = rules.apply_to_words(out, lambda w, f=fn: f(w, variant))
            if not reversible:
                result.lossless = False
                direction = "forward" if forward else "backward"
                msg = f"{edge_name} ({direction}) is lexical/lossy"
                if edge.note:
                    msg += f": {edge.note}"
                if msg not in result.warnings:
                    result.warnings.append(msg)

        # month/season casing is a text-level (sentence-position) concern: AO1990
        # lowercases them mid-sentence, the older norms capitalise them.
        if steps:
            out = rules.recase_months(out, lowercase=(dst.era == Era.AO1990))
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
            w = rules.reform_1911_geminates(rules.reform_1911_digraphs(w), lex.wordset)
            # 1911 also introduced systematic graphic accents the rules can't derive;
            # restore them from the word list where unambiguous (fosforo -> fósforo).
            return rules.restore_accent(w, lex.accent_restore)

        def reform_1911_bwd(w: str, _v: Optional[str]) -> str:
            return lex.reform1911_new2old.get(w, w)

        # -- 1911 <-> 1945 (PT): the 1945 Convenção dropped the trema for Portugal
        #    (ü -> u); otherwise the PT spelling is unchanged across these eras.
        def identity(w: str, _v: Optional[str]) -> str:
            return w

        def pt_1945_fwd(w: str, _v: Optional[str]) -> str:
            return rules.ao1990_drop_trema(w)

        # -- 1911 <-> 1943 (BR) ----------------------------------------------
        def br_1943_fwd(w: str, _v: Optional[str]) -> str:
            w = lex.base_iv_drop.get(w, w)
            w = lex.divergence_pt2br.get(w, w)   # connosco->conosco, húmido->úmido
            return rules.nasal_vowel_to_br(w)

        def br_1943_bwd(w: str, _v: Optional[str]) -> str:
            w = lex.divergence_br2pt.get(w, w)
            w = lex.base_iv_drop_reverse.get(w, w)
            return rules.nasal_vowel_to_pt(w)

        # -- 1945 <-> 1973 (PT): subtonic-grave removal only. The differential
        #    circumflex (êle->ele) was already abolished for Portugal by the 1945
        #    Convenção (Base XXII), so it must NOT be applied on this edge.
        def accent_1973_fwd(w: str, _v: Optional[str]) -> str:
            return rules.strip_subtonic_grave(w)

        def accent_1973_bwd(w: str, _v: Optional[str]) -> str:
            return w  # subtonic graves cannot be reintroduced by rule

        # -- 1943 <-> 1971 (BR): differential-circumflex removal (êle->ele,
        #    govêrno->governo) + subtonic-grave removal. Trema survives until AO1990.
        def accent_1971_fwd(w: str, _v: Optional[str]) -> str:
            w = lex.accent_71_73_old2new.get(w, w)
            return rules.strip_subtonic_grave(w)

        def accent_1971_bwd(w: str, _v: Optional[str]) -> str:
            return lex.accent_71_73_new2old.get(w, w)

        # -- pre-AO90 PT <-> AO1990 PT ---------------------------------------
        def ao_pt_fwd(w: str, _v: Optional[str]) -> str:
            if w in lex.ao_pt_old2new:
                return lex.ao_pt_old2new[w]
            w = lex.differential_dropped.get(w, w)
            w = lex.hyphen_dropped.get(w, w)
            w = lex.base_iv_drop.get(w, w)
            w = rules.drop_silent_cp(w, lex.cp_keep_pt, lex.wordset)
            w = rules.ao1990_drop_trema(w)
            w = rules.ao1990_drop_accents(w)
            w = rules.ao1990_hyphen_rs(w)
            return w

        def ao_pt_bwd(w: str, _v: Optional[str]) -> str:
            if w in lex.ao_pt_new2old:
                return lex.ao_pt_new2old[w]
            w = lex.hyphen_dropped_reverse.get(w, w)
            w = lex.base_iv_drop_reverse.get(w, w)
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
            return w

        def ao_br_bwd(w: str, _v: Optional[str]) -> str:
            if w in lex.ao_br_new2old:
                return lex.ao_br_new2old[w]
            w = lex.hyphen_dropped_reverse.get(w, w)
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
            "pt_1911_to_1945": _Edge(pt_1945_fwd, identity, reversible_backward=False,
                                     note="the trema cannot be reintroduced by rule"),
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
