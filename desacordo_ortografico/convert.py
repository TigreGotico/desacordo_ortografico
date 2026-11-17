"""Convert text between Portuguese orthographic norms.

A conversion is a path through the norm graph (:mod:`desacordo_ortografico.eras`).
Each edge carries a *forward* (older->newer) and *backward* transform built from the
deterministic rules (:mod:`rules`) and the curated lexicons (:mod:`lexicon`). Where an
authoritative word map exists (the AO1990 edges) it is applied first and the rules act
only as a fallback for words the map does not cover.

Each edge is an ordered list of named feature steps (:data:`FEATURES`). A caller can
pass ``features=`` to run only some of them; by default every feature runs.

The 1911 edge reads the pre-1911 -> 1911 rows of the spelling table
(``data/spelling.json``, see :mod:`lexicon`). The forward pass reads every such row
(comsigo -> consigo, Formulário Ortográfico of 1911, Base XV). The backward pass reads
the curated rows only. The edges out of 1911, toward pt_1945 and br_1943, read the
reforma_1911 rows of the table (quási -> quase), then apply the rules of :mod:`rules`
that quote the Acordo Ortográfico of 1945 and the Formulário Ortográfico of 1943
(tambêm -> também).

Forward conversion (toward newer norms) is well defined. Backward conversion is, for
several edges, *lexical and lossy*: dropping a silent consonant or an accent throws
away information that no rule can recover. The :class:`ConversionResult` reports this
via ``lossless`` and ``warnings`` instead of silently guessing.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Collection, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from . import rules
from .eras import NORMS, Era, Norm, Variant, find_path
from .lexicon import AO_ROW_CLASSES, Lexicon, ao_row_class, get_lexicon

WordFn = Callable[[str], str]

#: Every feature an edge can apply. ``convert(..., features=...)`` takes a subset.
FEATURES: FrozenSet[str] = frozenset({
    # Reforma de 1911
    "1911-word-map", "1911-digraphs", "1911-geminates", "1911-accent-restore",
    # trema (PT 1945, AO1990)
    "trema",
    # the edges out of 1911 (BR 1943, PT 1945): the word rows, the oxytones in -êm, the
    # grave on a u after q or g, the initial sc, and the PT 1945 differential circumflex
    "post-1911-word-map", "oxytone-em", "grave-u", "initial-sc", "differential-1945",
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
    # the ABL VOLP decisions for pt-BR words
    "volp",
    # month casing (text level)
    "months",
})


@dataclass
class _Pass:
    """One direction of an edge.

    A word that ``table`` holds is owned by the table: it gets the table value when the
    feature ``table_feature(word)`` is enabled, and stays as written otherwise. Every
    other word runs through ``steps`` in order, each step only when its feature is
    enabled. With ``plurals`` the table also owns the regular plural of each word it
    holds. A word for which ``skip`` is true runs no step.
    """

    steps: List[Tuple[str, WordFn]] = field(default_factory=list)
    table: Optional[Mapping[str, str]] = None
    table_feature: Optional[Callable[[str], str]] = None
    plurals: bool = False
    skip: Optional[Callable[[str], bool]] = None

    def apply(self, word: str, enabled: FrozenSet[str]) -> str:
        if self.table is not None:
            form = (rules.lookup_with_plural(word, self.table) if self.plurals
                    else self.table.get(word))
            if form is not None:
                return form if self.table_feature(word) in enabled else word
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
        # pt-PT text reaches ao1990-br through the divergence edge; there a VOLP row whose
        # bare form is another pt-PT word (fato, the suit) keeps it
        from_pt = dst.id == "ao1990-br" and "volp" in enabled and any(
            name == "ptbr_divergence" and fwd for name, _frm, fwd in steps)
        pt_words = self.lex.ao_br_volp_pt_words if from_pt else {}
        result = ConversionResult(text=text, source=src.id, target=dst.id)
        if not steps:
            return result

        # A token in capitals marks an acronym only in mixed-case text. Text in capitals
        # throughout converts each token like the same word in lowercase. The test reads
        # the words alone: Python counts º and ª as lowercase letters (ART. 2.º).
        is_word = None if "".join(rules.words(text)).isupper() else self.lex.is_known
        # A word whose written form the official vocabulary of the target variety gives
        # stays as written on every edge, whatever features run: a form the VOLP lists
        # toward pt-BR (facto, cetro, cato, óptica), the form with the consonant of a pt-PT
        # dual cell toward pt-PT (sector, carácter). Only the dual choice after the edges
        # rewrites it, to the form with the consonant (ruling for duals).
        # AO1990 Base XXI lets a name keep the spelling it is written in. Toward pt-BR a
        # name whose written form the VOLP lists is held and also skips that choice
        # (pt_1973 receptores -> ao1990-pt recetores, which the VOLP rejects). For each
        # word of ``out``, ``written`` holds the word of the source that it comes from.
        valid = (self.lex.ao_br_volp_held if dst.id == "ao1990-br"
                 else self.lex.ao_pt_dual_forms if dst.id == "ao1990-pt" else frozenset())
        written = rules.words(text)
        named = rules.names(text) if dst.id == "ao1990-br" and "volp" in enabled else [False] * len(written)
        kept = [n and w.lower() in self.lex.ao_br_volp_listed for w, n in zip(written, named)]
        held = [k or w.lower() in valid for w, k in zip(written, kept)]
        out = text
        for edge_name, _frm, forward in steps:
            edge = self._edges[edge_name]
            step_pass = edge.forward if forward else edge.backward
            reversible = edge.reversible_forward if forward else edge.reversible_backward
            guess = edge_name == "reform_1911" and forward and "1911-accent-restore" in enabled
            # the word pass rewrites letters inside each word only, so the tags aligned to
            # the words before it still line up one to one with the words after it
            tags = rules.align_tags(rules.words(out), pos_tags or []) if guess else []
            own = pt_words if edge_name == "ptbr_divergence" else {}
            out, sources = rules.map_words(
                out, lambda i, w, p=step_pass, k=own: None if held[i] else k.get(w) or p.apply(w, enabled), is_word)
            written, held, named, kept = ([x[i] for i in sources] for x in (written, held, named, kept))
            if guess:
                variety = "br" if dst.variant == Variant.BR else "pt"
                out = rules.guess_accents(out, self.lex.accent_restore, self.lex.accent_restore_nominal,
                                          self.lex.accent_restore_singular, tags, variety,
                                          {i for i, h in enumerate(held) if h})
            if not reversible:
                result.lossless = False
                direction = "forward" if forward else "backward"
                msg = f"{edge_name} ({direction}) is lexical/lossy"
                if edge.note:
                    msg += f": {edge.note}"
                if msg not in result.warnings:
                    result.warnings.append(msg)

        # Base IV 1º c: where both forms of a dual cell are valid in the target variety,
        # an AO1990 target writes the form with the consonant (sector, liquefacto). For
        # pt-BR the VOLP decides a word it holds before the tugalex dual cells do.
        if dst.era == Era.AO1990:
            br = dst.variant == Variant.BR
            duals = ((self.lex.ao_br_dual_full if br else self.lex.ao_pt_dual_full)
                     if "silent-cp" in enabled else {})
            volp = self.lex.ao_br_volp if br and "volp" in enabled else {}

            # Base XVI: a listed prefix joins its second element. The join runs here, once,
            # on the words of the target, so the VOLP and the dual cells decide each element
            # first (foto-recetores -> foto-receptores -> fotorreceptores). The older norms
            # keep the hyphen (1945 Base XXIX, 1943 Formulário 5.º a), so only an AO1990
            # target joins, and a route between two older norms through AO1990 does not.
            # A row of an AO1990 map whose feature is off stays as written (auto-retrato
            # without ao-map-join).
            maps = ((self.lex.ao_pt_old2new, self.lex.ao_pt_row_class),
                    (self.lex.ao_br_old2new, self.lex.ao_br_row_class))

            # a loanword that the vocabulary of the target variety lists with its hyphen
            # keeps it (VOP anti-apartheid, VOLP mini-system)
            loanwords = self.lex.hyphen_loanwords["br" if br else "pt"]

            def join(w: str) -> str:
                if "prefix-rs" not in enabled or rules.lookup_with_plural(w, loanwords) or any(
                        w in table and f"ao-map-{classes[w]}" not in enabled for table, classes in maps):
                    return w
                return rules.ao1990_hyphen_rs(w, co_drops_h=br)

            def choose(w: str) -> Optional[str]:
                return pt_words.get(w) or volp.get(w) or duals.get(w)

            # each element of a compound drops its mute c or p as a word does, by the pt-PT
            # map (co-directores -> co-diretores) or by the VOLP (peixe-eléctricos ->
            # peixe-elétricos)
            def drop(w: str) -> str:
                if br:
                    return rules.drop_silent_cp(w, volp) if volp else w
                return rules.drop_silent_cp(w, self.lex.ao_pt_old2new) if "silent-cp" in enabled else w

            def element(w: str) -> str:
                return choose(drop(w)) or drop(w)

            # a name keeps a form the VOLP lists and takes the VOLP form of any other
            def choose_for_name(w: str) -> Optional[str]:
                return None if w in self.lex.ao_br_volp_listed else pt_words.get(w) or volp.get(w)

            def choose_word(i: int, w: str) -> Optional[str]:
                if kept[i]:
                    return None
                if "-" in w:
                    # a compound that the map or the VOLP holds whole drops as one word
                    # (peixe-eléctricos), any other each element on its own (setor-chave)
                    whole = drop(w)
                    form = choose(w) or choose(whole) or (
                        whole if whole != w else "-".join(map(element, w.split("-"))))
                else:
                    form = choose(w) or w
                # the joined word is one word, and the VOLP or a dual cell decides it
                # (co-factores -> cofactores -> cofatores, codialetos -> codialectos)
                if (solid := join(form)) != form:
                    form = choose(solid) or solid
                # a name gains no c or p from a dual: it has no more than the source wrote
                if named[i] and sum(map(form.count, "cp")) > sum(map(written[i].lower().count, "cp")):
                    form = join(choose_for_name(w) or "-".join(choose_for_name(p) or p for p in w.split("-")))
                return form

            if volp or duals or "prefix-rs" in enabled:
                out = rules.map_words(out, choose_word, is_word)[0]

        # the 1943 Formulário joins a prefix that it does not list (46 5.º, 22), so br_1971
        # writes microssistema, as the Pequeno Vocabulário of 1943 writes microssismo. Its
        # 40 lets a firm keep its registered spelling, so a name does not join (a
        # Micro-Sistemas). A loanword that the VOLP lists with its hyphen keeps it
        # (mini-system)
        if dst.id == "br_1971" and "prefix-rs" in enabled:
            capital = rules.names(out)
            loanwords = self.lex.hyphen_loanwords["br"]
            out = rules.map_words(
                out, lambda i, w: None if capital[i] or rules.lookup_with_plural(w, loanwords)
                else rules.br_1943_prefix_join(w), is_word)[0]

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

        # -- 1911: the word maps first; the rules are a fallback for other words. They
        #    leave a loanword or a foreign name alone (rules.is_foreign_spelling). 1911
        #    also introduced graphic accents the rules can't derive; convert() restores
        #    them after this pass, from the word list and the context (fosforo -> fósforo).
        reform_1911 = _Edge(
            _Pass(
                steps=[
                    ("1911-digraphs", rules.reform_1911_digraphs),
                    ("1911-geminates", lambda w: rules.reform_1911_geminates(w, lex.wordset)),
                ],
                table=lex.reform1911_forward, table_feature=word_map_1911,
                skip=rules.is_foreign_spelling,
            ),
            _Pass(table=lex.reform1911_new2old, table_feature=word_map_1911),
            reversible_backward=False,
            note="1911 digraph simplification (ph/th/y) cannot be reversed by rule",
        )

        # -- 1911 -> 1945 (PT) and 1911 -> 1943 (BR): the word rows of the spelling
        #    table, then the rules; rules.py quotes the clause of each. The backward pass
        #    reads the curated rows inverted, as the backward 1911 pass does, and like it
        #    reads no plural. The rules stay one-way: an inverted initial-sc would give
        #    scenoura from cenoura.
        def post_1911_word_map(_w: str) -> str:
            return "post-1911-word-map"

        def from_1911(rows: Mapping[str, str]) -> WordFn:
            # only a form that ends in a, e or o takes the plural -s: the noun scetro
            # (scetros), and not the adverbs quási, tam, quam or the verb forms teem, veem
            nouns = {form: value for form, value in rows.items() if form[-1:] in "aeo"}

            def read(word: str) -> str:
                parts = rules._SEGMENT_SEP.split(word)
                if len(parts) > 1 and len({p.removesuffix("s") for p in parts}) == 1:  # tam-tams
                    return word
                return rules.per_segment(
                    word, lambda p: rows.get(p) or rules.lookup_with_plural(p, nouns) or p)

            return read

        pt_1911_to_1945 = _Edge(
            _Pass(steps=[
                ("post-1911-word-map", from_1911(lex.reform1911_to_1945)),
                ("initial-sc", rules.drop_initial_sc),
                ("oxytone-em", rules.oxytone_em_acute),
                ("grave-u", rules.drop_grave_u),
                ("differential-1945", lambda w: rules.drop_differential_1945(w, lex.is_listed)),
                ("trema", rules.ao1990_drop_trema),
            ]),
            _Pass(table=lex.reform1911_from_1945, table_feature=post_1911_word_map),
            reversible_backward=False,
            note="the trema cannot be reintroduced by rule",
        )

        br_1911_to_1943 = _Edge(
            _Pass(steps=[
                ("post-1911-word-map", from_1911(lex.reform1911_to_1943)),
                ("initial-sc", rules.drop_initial_sc),
                ("oxytone-em", rules.oxytone_em_acute),
                ("grave-u", rules.grave_u_to_trema),
                ("base-iv", get(lex.base_iv_drop)),
                ("ptbr-divergence", get(lex.divergence_pt2br)),  # connosco->conosco
                ("nasal-vowel", rules.nasal_vowel_to_br),
            ]),
            _Pass(steps=[
                ("ptbr-divergence", ptbr_before_ao1990),
                ("base-iv", get(lex.base_iv_drop_reverse)),
                ("nasal-vowel", rules.nasal_vowel_to_pt),
            ], table=lex.reform1911_from_1943, table_feature=post_1911_word_map),
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
        #    sôbre->sobre) + subtonic-grave removal. Trema survives until AO1990.
        #    Lei n.º 5.765, de 18 de dezembro de 1971, Art. 1.º: "fica abolido [...] o
        #    acento circunflexo diferencial na letra e e na letra o, a sílaba tônica das
        #    palavras homógrafas de outras em que são abertas a letra e e a letra o,
        #    exceção feita da forma pôde, que se acentuará por oposição a pode". The
        #    table lists words with that accent in the 1943 Formulário (14.ª). Its
        #    inverse is the backward map, so a word whose bare form is the more frequent
        #    reading (corte, deveras, colher) has no row.
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
