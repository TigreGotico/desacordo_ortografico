"""Convert text between Portuguese orthographic norms.

A conversion is a path through the norm graph (:mod:`desacordo_ortografico.eras`).
Each edge carries a *forward* (older->newer) and *backward* transform built from the
deterministic rules (:mod:`rules`) and the curated/`tugalex` lexicons
(:mod:`lexicon`). Where an authoritative word map exists (the AO1990 edges, via
``tugalex``) it is applied first and the rules act only as a fallback for words the
map does not cover.

Each edge is an ordered list of named feature steps (:data:`FEATURES`). A caller can
pass ``features=`` to run only some of them; by default every feature runs.

The 1911 edge reads two word maps. The first is the 1911 map of this package
(``data/reform_1911_irregular.json``). The second is the ``archaisms.csv`` list of
``tugalex`` (``TugaLexicon.archaic_words``), whose rows cite the base of the Formulário
Ortográfico of 1911 that changes each word (comsigo -> consigo, Base XV). A row gives
its modern pt-PT form, and that form can also carry a change made after 1911, so
:func:`archaism_row_class` sorts the rows and only two classes enter the 1911 map. A
row also stays out when the Brazilian edges do not turn the form it gives the 1911 map
into its pt-BR form. That check tests only the rows whose form for the 1911 map differs
from their pt-BR form. For the other rows it only shows that the Brazilian edges keep
the word, and it says nothing about the 1911 form. Where both maps hold a word, the map
of this package decides. The backward pass reads the map of this package only.

Forward conversion (toward newer norms) is well defined. Backward conversion is, for
several edges, *lexical and lossy*: dropping a silent consonant or an accent throws
away information that no rule can recover. The :class:`ConversionResult` reports this
via ``lossless`` and ``warnings`` instead of silently guessing.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Collection, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from . import rules
from .eras import NORMS, Era, Norm, Variant, find_path
from .lexicon import AO_ROW_CLASSES, Lexicon, ao_row_class, deaccent, get_lexicon

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


#: The classes of a tugalex archaism row, see :func:`archaism_row_class`.
ARCHAISM_ROW_CLASSES = ("1911", "ao1990-map", "ao1990-cp", "ao1990-differential", "sc", "circumflex")

#: A Base IV 1º sequence of the AO1990 after a vowel: cc, cç, ct, pc, pç or pt.
_CP_SEQUENCE = re.compile(r"(?<=[aeiou])[cp][cçt]")


def archaism_row_class(archaic: str, modern: str, lex: Lexicon) -> str:
    """Classify a tugalex archaism row (``archaic`` -> its modern pt-PT form ``modern``)
    by the reform that its modern form rests on.

    ``1911``: no check below finds a post-1911 change, so the modern form stands for the
    1911 form (comsigo -> consigo, phosphoro -> fósforo). The checks do not find every
    accent: Base VII of 1911 writes "êle", and the row elle -> ele is in this class.
    ``ao1990-map``: the AO1990 pt-PT word map lists the modern form, so the 1911 form is the
    pre-AO1990 form of that map (architecto -> arquiteto, before AO1990 arquitecto).
    ``ao1990-differential``: the modern form is the bare form of a differential accent
    that the AO1990 dropped (pello -> pelo, before AO1990 pêlo).
    ``ao1990-cp``: the modern form lacks the c or p of a Base IV 1º sequence that the
    archaic form keeps after the regular 1911 rules, and the AO1990 map does not list it.
    1911 Base VIII drops such a consonant where it is silent (auctor -> autor), Base IX
    keeps it where it changes the vowel before it (affectando -> afectando, AO1990
    afetando), and no table here tells the two apart.
    ``sc``: the archaic form starts with the group sc and the modern form does not. Base
    XI of 1911 keeps that group (scena, sciência), and later accords drop it (cintilar).
    ``circumflex``: the archaic form has more ê or ô than the modern form. Base XXVIII
    of 1911 marks the closed e or o of a homograph ("rêgo, substantivo, e rego,
    verbo"), later laws drop that accent (sêcco -> seco, 1911 sêco), and no table here
    gives the 1911 form of every such row.

    Only the ``1911`` and ``ao1990-map`` rows can enter the 1911 word map
    (``OrthographyConverter``).
    """
    if archaic.startswith("sc") and not modern.startswith("sc"):
        return "sc"
    if modern in lex.differential_dropped.values() or modern in lex.differential_restore:
        return "ao1990-differential"
    if modern in lex.ao_pt_new2old:
        return "ao1990-map"
    regular = rules.reform_1911_geminates(rules.reform_1911_digraphs(archaic))
    if len(_CP_SEQUENCE.findall(deaccent(regular))) > len(_CP_SEQUENCE.findall(deaccent(modern))):
        return "ao1990-cp"
    if _circumflexes(archaic) > _circumflexes(modern):
        return "circumflex"
    return "1911"


def _circumflexes(word: str) -> int:
    """The number of ê and ô in ``word``, the closed vowels of Base XXVIII."""
    return word.count("ê") + word.count("ô")


@dataclass
class _Pass:
    """One direction of an edge.

    A word that ``table`` holds is owned by the table: it gets the table value when the
    feature ``table_feature(word)`` is enabled, and stays as written otherwise. Every
    other word runs through ``steps`` in order, each step only when its feature is
    enabled. With ``plurals`` the table also owns the regular plural of each word it
    holds.
    """

    steps: List[Tuple[str, WordFn]] = field(default_factory=list)
    table: Optional[Mapping[str, str]] = None
    table_feature: Optional[Callable[[str], str]] = None
    plurals: bool = False

    def apply(self, word: str, enabled: FrozenSet[str]) -> str:
        if self.table is not None:
            form = (rules.lookup_with_plural(word, self.table) if self.plurals
                    else self.table.get(word))
            if form is not None:
                return form if self.table_feature(word) in enabled else word
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
        pos_tags: Optional[Sequence[Tuple[str, str]]] = None,
    ) -> ConversionResult:
        """Convert ``text`` from ``source`` to ``target``.

        ``features`` names the :data:`FEATURES` to apply. ``None`` applies all of them.
        An unknown name raises ``ValueError``.

        ``pos_tags`` holds the ``(word, UPOS)`` pairs of ``text`` from a part-of-speech
        tagger, as ``tugatagger.TugaTagger.tag(text)`` returns them. The 1911 accent
        guess gives a bare form that is otherwise only a verb form its accent after a
        determiner or a preposition (a historia -> a história), and keeps it bare after a
        clitic pronoun. A tag decides only the words that this rule leaves undecided:
        NOUN or ADJ gives the accent. The target's variety decides when a bare article
        is the article and when it is the pronoun, see :func:`rules.guess_accents`.
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

        # A token in capitals marks an acronym only in mixed-case text. Text in capitals
        # throughout converts each token like the same word in lowercase. The test reads
        # the words alone: Python counts º and ª as lowercase letters (ART. 2.º).
        is_word = None if "".join(rules.words(text)).isupper() else self.lex.is_known
        out = text
        for edge_name, _frm, forward in steps:
            edge = self._edges[edge_name]
            step_pass = edge.forward if forward else edge.backward
            reversible = edge.reversible_forward if forward else edge.reversible_backward
            guess = edge_name == "reform_1911" and forward and "1911-accent-restore" in enabled
            # the word pass rewrites letters inside each word only, so the tags aligned to
            # the words before it still line up one to one with the words after it
            tags = rules.align_tags(rules.words(out), pos_tags or []) if guess else []
            out = rules.apply_to_words(out, lambda w, p=step_pass: p.apply(w, enabled), is_word)
            if guess:
                variety = "br" if dst.variant == Variant.BR else "pt"
                out = rules.guess_accents(out, self.lex.accent_restore, self.lex.accent_restore_nominal,
                                          self.lex.accent_restore_singular, tags, variety)
            if not reversible:
                result.lossless = False
                direction = "forward" if forward else "backward"
                msg = f"{edge_name} ({direction}) is lexical/lossy"
                if edge.note:
                    msg += f": {edge.note}"
                if msg not in result.warnings:
                    result.warnings.append(msg)

        # Base IV 1º c: where both forms of a dual cell are valid in the target variety,
        # an AO1990 target writes the form with the consonant (sector, liquefacto).
        if "silent-cp" in enabled and dst.era == Era.AO1990:
            duals = self.lex.ao_br_dual_full if dst.variant == Variant.BR else self.lex.ao_pt_dual_full
            # each element of a compound too (setor-chave), unless the compound is a cell
            out = rules.apply_to_words(
                out, lambda w: duals.get(w) or "-".join(duals.get(p, p) for p in w.split("-")), is_word)

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
            return lambda w: f"ao-map-{ao_row_class(to_old[w], w)}"

        def word_map_1911(_w: str) -> str:
            return "1911-word-map"

        def ptbr_divergence(_w: str) -> str:
            return "ptbr-divergence"

        def ptbr_before_ao1990(w: str) -> str:
            # before AO1990 the European norm wrote the consonant too: a pt-PT form that
            # only AO1990 writes (receção) is no older European form (recepção)
            pt = lex.divergence_br2pt.get(w, w)
            return w if pt in lex.ao_pt_new2old else pt

        # -- 1911: the word maps first; the rules are a fallback for other words. 1911
        #    also introduced graphic accents the rules can't derive; convert() restores
        #    them after this pass, from the word list and the context (fosforo -> fósforo).
        #    The tugalex archaisms join the forward map at the end of this method. The
        #    backward pass reads the map of this package only: several archaic forms of
        #    the tugalex list share one modern form (architectura, architetura).
        reform_1911 = _Edge(
            _Pass(
                steps=[
                    ("1911-digraphs", rules.reform_1911_digraphs),
                    ("1911-geminates", lambda w: rules.reform_1911_geminates(w, lex.wordset)),
                ],
                table=lex.reform1911_old2new, table_feature=word_map_1911,
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
                ("ptbr-divergence", ptbr_before_ao1990),
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
                    ("silent-cp", lambda w: rules.drop_silent_cp(w, lex.ao_pt_old2new)),
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
                    ("silent-cp", lambda w: rules.restore_silent_cp(w, lex.ao_pt_new2old)),
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
                  table=lex.divergence_pt2br, table_feature=ptbr_divergence, plurals=True),
            _Pass(steps=[("nasal-vowel", rules.nasal_vowel_to_pt)],
                  table=lex.divergence_br2pt, table_feature=ptbr_divergence, plurals=True),
        )

        # -- the tugalex archaisms in the 1911 forward map. The European and the
        #    Brazilian targets share the 1911 form, so a row stays out when the Brazilian
        #    edges do not turn its form into its pt-BR form. architecto enters (arquitecto,
        #    Brazil arquiteto); affectado stays out, because no Brazilian table drops the c
        #    of afectado. Where the form and the pt-BR form are the same word, the check
        #    only shows that the Brazilian edges keep that word.
        def brazilian(word: str) -> str:
            for edge in (br_1911_to_1943, accent_1971, ao1990_br):
                word = edge.forward.apply(word, FEATURES)
            return word

        archaisms: Dict[str, str] = {}
        tuga = lex.tuga
        for archaic, modern in (tuga.archaic_words if tuga else {}).items():
            row_class = archaism_row_class(archaic, modern, lex)
            if row_class == "1911":
                form = modern
            elif row_class == "ao1990-map":
                form = lex.ao_pt_new2old[modern]
            else:
                continue
            if brazilian(form) == tuga.archaic_words_br[archaic]:
                archaisms[archaic] = form
        reform_1911.forward.table = {**archaisms, **lex.reform1911_old2new}

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
    pos_tags: Optional[Sequence[Tuple[str, str]]] = None,
) -> str:
    """Convert ``text`` from ``source`` to ``target`` and return the string.

    ``features`` names the :data:`FEATURES` to apply; ``None`` applies all of them.
    ``pos_tags`` holds the ``(word, UPOS)`` pairs of ``text``; see
    :meth:`OrthographyConverter.convert`. For the full result (warnings, dual-form
    alternatives) use :meth:`OrthographyConverter.convert`.
    """
    return _converter().convert(text, source, target, variant, features, pos_tags).text
