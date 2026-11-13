"""Convert text between Portuguese orthographic norms.

A conversion is a path through the norm graph (:mod:`desacordo_ortografico.eras`).
Each edge carries a *forward* (older->newer) and *backward* transform built from the
deterministic rules (:mod:`rules`) and the curated/`tugalex` lexicons
(:mod:`lexicon`). Where an authoritative word map exists (the AO1990 edges, via
``tugalex``) it is applied first and the rules act only as a fallback for words the
map does not cover.

Each edge is an ordered list of named feature steps (:data:`FEATURES`). A caller can
pass ``features=`` to run only some of them; by default every feature runs.

Forward conversion (toward newer norms) is well defined. Backward conversion is, for
several edges, *lexical and lossy*: dropping a silent consonant or an accent throws
away information that no rule can recover. The :class:`ConversionResult` reports this
via ``lossless`` and ``warnings`` instead of silently guessing.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Collection, Dict, FrozenSet, List, Mapping, Optional, Tuple

from . import rules
from .eras import NORMS, Era, Norm, find_path
from .lexicon import AO_ROW_CLASSES, Lexicon, get_lexicon

WordFn = Callable[[str], str]

#: Every feature an edge can apply. ``convert(..., features=...)`` takes a subset.
FEATURES: FrozenSet[str] = frozenset({
    # Reforma de 1911
    "1911-word-map", "1911-digraphs", "1911-geminates", "1911-accent-restore",
    # trema (PT 1945, AO1990)
    "trema",
    # subtonic grave accents (PT 1973, BR 1971)
    "subtonic-grave",
    # BR 1943 and the AO1990 PT/BR divergence
    "base-iv", "ptbr-divergence", "nasal-vowel",
    # BR 1971 differential circumflex
    "differential-1971",
    # the tugalex AO1990 word maps, by row class
    *(f"ao-map-{cls}" for cls in AO_ROW_CLASSES),
    # AO1990 rules and curated lists
    "differential", "hyphen-lexical", "silent-cp", "diphthong-accent", "hiatus-accent",
    "prefix-rs",
    # month casing (text level)
    "months",
})


@dataclass
class _Pass:
    """One direction of an edge.

    A word that ``table`` holds is owned by the table: it gets the table value when the
    feature ``table_feature(word)`` is enabled, and stays as written otherwise. Every
    other word runs through ``steps`` in order, each step only when its feature is
    enabled. A word for which ``skip`` is true runs no step.
    """

    steps: List[Tuple[str, WordFn]] = field(default_factory=list)
    table: Optional[Mapping[str, str]] = None
    table_feature: Optional[Callable[[str], str]] = None
    skip: Optional[Callable[[str], bool]] = None

    def apply(self, word: str, enabled: FrozenSet[str]) -> str:
        if self.table is not None and word in self.table:
            return self.table[word] if self.table_feature(word) in enabled else word
        if self.skip is not None and self.skip(word):
            return word
        for feature, fn in self.steps:
            if feature in enabled:
                word = fn(word)
        return word


@dataclass
class _Edge:
    """Forward/backward passes for one graph edge."""

    forward: _Pass
    backward: _Pass
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
        features: Optional[Collection[str]] = None,
    ) -> ConversionResult:
        """Convert ``text`` from ``source`` to ``target``.

        ``features`` names the :data:`FEATURES` to apply. ``None`` applies all of them.
        An unknown name raises ``ValueError``.
        """
        enabled = _enabled(features)
        text = unicodedata.normalize("NFC", text)
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
            step_pass = edge.forward if forward else edge.backward
            reversible = edge.reversible_forward if forward else edge.reversible_backward
            out = rules.apply_to_words(out, lambda w, p=step_pass: p.apply(w, enabled))
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
        if "months" in enabled:
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

        def get(table: Mapping[str, str]) -> WordFn:
            return lambda w: table.get(w, w)

        def ao_row(classes: Mapping[str, str], to_old: Optional[Mapping[str, str]] = None):
            if to_old is None:
                return lambda w: f"ao-map-{classes[w]}"
            return lambda w: f"ao-map-{classes[to_old[w]]}"

        def word_map_1911(_w: str) -> str:
            return "1911-word-map"

        def ptbr_divergence(_w: str) -> str:
            return "ptbr-divergence"

        # -- 1911: the word map first; the rules are a fallback for other words. They
        #    leave a loanword or a foreign name alone (rules.is_foreign_spelling). 1911
        #    also introduced graphic accents the rules can't derive; they are restored
        #    from the word list where unambiguous (fosforo -> fósforo).
        reform_1911 = _Edge(
            _Pass(
                steps=[
                    ("1911-digraphs", rules.reform_1911_digraphs),
                    ("1911-geminates", lambda w: rules.reform_1911_geminates(w, lex.wordset)),
                    ("1911-accent-restore", lambda w: rules.restore_accent(w, lex.accent_restore)),
                ],
                table=lex.reform1911_old2new, table_feature=word_map_1911,
                skip=rules.is_foreign_spelling,
            ),
            _Pass(table=lex.reform1911_new2old, table_feature=word_map_1911),
            reversible_backward=False,
            note="1911 digraph simplification (ph/th/y) cannot be reversed by rule",
        )

        # -- 1911 <-> 1945 (PT): the 1945 Convenção dropped the trema for Portugal
        #    (ü -> u); otherwise the PT spelling is unchanged across these eras.
        pt_1911_to_1945 = _Edge(
            _Pass(steps=[("trema", rules.ao1990_drop_trema)]),
            _Pass(),
            reversible_backward=False,
            note="the trema cannot be reintroduced by rule",
        )

        # -- 1911 <-> 1943 (BR) ----------------------------------------------
        br_1911_to_1943 = _Edge(
            _Pass(steps=[
                ("base-iv", get(lex.base_iv_drop)),
                ("ptbr-divergence", get(lex.divergence_pt2br)),  # connosco->conosco
                ("nasal-vowel", rules.nasal_vowel_to_br),
            ]),
            _Pass(steps=[
                ("ptbr-divergence", get(lex.divergence_br2pt)),
                ("base-iv", get(lex.base_iv_drop_reverse)),
                ("nasal-vowel", rules.nasal_vowel_to_pt),
            ]),
            reversible_backward=False,
            note="silent-consonant restoration is lexical",
        )

        # -- 1945 <-> 1973 (PT): subtonic-grave removal only. The differential
        #    circumflex (êle->ele) was already abolished for Portugal by the 1945
        #    Convenção (Base XXII), so it must NOT be applied on this edge. Subtonic
        #    graves cannot be reintroduced by rule.
        accent_1973 = _Edge(
            _Pass(steps=[("subtonic-grave", rules.strip_subtonic_grave)]),
            _Pass(),
            reversible_backward=False,
            note="subtonic grave accents cannot be reintroduced by rule",
        )

        # -- 1943 <-> 1971 (BR): differential-circumflex removal (êle->ele,
        #    govêrno->governo) + subtonic-grave removal. Trema survives until AO1990.
        accent_1971 = _Edge(
            _Pass(steps=[
                ("differential-1971", get(lex.accent_71_73_old2new)),
                ("subtonic-grave", rules.strip_subtonic_grave),
            ]),
            _Pass(steps=[("differential-1971", get(lex.accent_71_73_new2old))]),
            reversible_backward=False,
            note="subtonic grave accents cannot be reintroduced by rule",
        )

        # -- pre-AO90 PT <-> AO1990 PT ---------------------------------------
        ao1990_pt = _Edge(
            _Pass(
                steps=[
                    ("differential", lambda w: rules.drop_differential(w, lex.differential_dropped)),
                    ("hyphen-lexical", get(lex.hyphen_dropped)),
                    ("base-iv", get(lex.base_iv_drop)),
                    ("silent-cp", lambda w: rules.drop_silent_cp(w, lex.cp_keep_pt, lex.wordset)),
                    ("trema", rules.ao1990_drop_trema),
                    ("diphthong-accent", rules.ao1990_drop_diphthong_accent),
                    ("hiatus-accent", rules.ao1990_drop_hiatus_accent),
                    ("prefix-rs", rules.ao1990_hyphen_rs),
                ],
                table=lex.ao_pt_old2new, table_feature=ao_row(lex.ao_pt_row_class),
            ),
            _Pass(
                steps=[
                    ("hyphen-lexical", get(lex.hyphen_dropped_reverse)),
                    ("base-iv", get(lex.base_iv_drop_reverse)),
                ],
                table=lex.ao_pt_new2old,
                table_feature=ao_row(lex.ao_pt_row_class, lex.ao_pt_new2old),
            ),
            reversible_backward=False,
            note="dropped accents/consonants are restored from a lexicon, not a rule",
        )

        # -- pre-AO90 BR <-> AO1990 BR ---------------------------------------
        ao1990_br = _Edge(
            _Pass(
                steps=[
                    ("differential", lambda w: rules.drop_differential(w, lex.differential_dropped)),
                    ("hyphen-lexical", get(lex.hyphen_dropped)),
                    ("trema", rules.ao1990_drop_trema),
                    ("diphthong-accent", rules.ao1990_drop_diphthong_accent),
                    ("hiatus-accent", rules.ao1990_drop_hiatus_accent),
                    ("prefix-rs", rules.ao1990_hyphen_rs),
                ],
                table=lex.ao_br_old2new, table_feature=ao_row(lex.ao_br_row_class),
            ),
            _Pass(
                steps=[("hyphen-lexical", get(lex.hyphen_dropped_reverse))],
                table=lex.ao_br_new2old,
                table_feature=ao_row(lex.ao_br_row_class, lex.ao_br_new2old),
            ),
            reversible_backward=False,
            note="dropped accents/trema are restored from a lexicon, not a rule",
        )

        # -- AO1990 PT <-> AO1990 BR (lateral divergence) --------------------
        ptbr = _Edge(
            _Pass(steps=[("nasal-vowel", rules.nasal_vowel_to_br)],
                  table=lex.divergence_pt2br, table_feature=ptbr_divergence),
            _Pass(steps=[("nasal-vowel", rules.nasal_vowel_to_pt)],
                  table=lex.divergence_br2pt, table_feature=ptbr_divergence),
        )

        return {
            "reform_1911": reform_1911,
            "pt_1911_to_1945": pt_1911_to_1945,
            "br_1911_to_1943": br_1911_to_1943,
            "accent_1973": accent_1973,
            "accent_1971": accent_1971,
            "ao1990_pt": ao1990_pt,
            "ao1990_br": ao1990_br,
            "ptbr_divergence": ptbr,
        }


def _enabled(features: Optional[Collection[str]]) -> FrozenSet[str]:
    if features is None:
        return FEATURES
    if isinstance(features, str):
        raise TypeError("features must be a collection of feature names, not a string")
    enabled = frozenset(features)
    unknown = enabled - FEATURES
    if unknown:
        raise ValueError(
            f"Unknown feature(s): {', '.join(sorted(unknown))}. "
            f"Valid features: {', '.join(sorted(FEATURES))}"
        )
    return enabled


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
    features: Optional[Collection[str]] = None,
) -> str:
    """Convert ``text`` from ``source`` to ``target`` and return the string.

    ``features`` names the :data:`FEATURES` to apply; ``None`` applies all of them.
    For the full result (warnings, dual-form alternatives) use
    :meth:`OrthographyConverter.convert`.
    """
    return _converter().convert(text, source, target, variant, features).text
