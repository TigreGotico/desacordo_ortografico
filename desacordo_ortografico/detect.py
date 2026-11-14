"""Detect which Portuguese orthography a text is written in.

The detector is marker-based: it scans the tokens for orthographic evidence and scores
the candidate norms. Distinguishing every historical era from spelling alone is not
always possible (1911 and 1945 PT spell most words identically), so the detector
reports at the granularity that orthography actually supports: pre-1911 *etymological*,
*pre-AO1990* (PT/BR), and *AO1990* (PT/BR), with the variant left unset when no
distinguishing marker is present.

It calls the sister-language :mod:`guard` first; a :class:`~guard.NotPortuguese` result
short-circuits everything else.

Pre-1911 evidence is a listed archaic form: a word of the 1911 word map of this package
(``data/reform_1911_irregular.json``) or of the ``archaisms.csv`` list of tugalex
(``TugaLexicon.archaic_words``). The tugalex list is read for each part of a hyphenated
or elided token (d'ella). Their source is the Formulário Ortográfico of 1911 (Portal da
Língua Portuguesa, ILTEC): base I proscribes k, w and y in Portuguese words ("y por i
... lira, fisiologia"), base VI drops the h of rh and th and writes ph as f ("teatro",
"O grupo ph será expresso por f"), and base VII doubles no consonant except rr, ss, mm
and nn where they are pronounced ("êle, ela, ... aparecer, ... atitude"), and base VIII
drops a silent consonant that does not change the vowel before it ("autor, restrito,
produto"). The tugalex list also rests on the Priberam dictionary for the modern forms
and on the IRN list of admitted given names. A spelling pattern alone is no evidence.
Base I applies to "palavras portuguesas, ou aportuguesadas", and its exception 1.ª
allows k, w and y in derivatives of foreign names ("Poderão usar-se essas letras";
kantismo, darwinismo, byroniano), so a foreign word or
name (the, Taylor, Mary) in a modern sentence is no pre-1911 spelling.

A listed form that spells a name is no evidence either. Base XXI of the Acordo
Ortográfico of 1990 (Portal da Língua Portuguesa text), "Das assinaturas e firmas": "Para
ressalva de direitos, cada qual poderá manter a escrita que, por costume ou registo
legal, adote na assinatura do seu nome. Com o mesmo fim, pode manter-se a grafia
original de quaisquer firmas comerciais, nomes de sociedades, marcas e títulos que
estejam inscritos em registo público." Base I 2.º a) keeps the letters of foreign
names: "Em antropónimos/antropônimos originários de outras línguas e seus derivados:
Franklin, frankliniano; Kant, kantismo; Darwin, darwinismo; Wagner, wagneriano; Byron,
byroniano; Taylor, taylorista". So a part of a word that the tugalex list holds gives no
pre-1911 evidence when it is inside a sentence and the word or the part starts with a
capital (Sant'Anna, d'Oliveira Paes, Victoria's Secret). The first word of a sentence
(after . ! ? … or a line break) keeps its evidence, and so does a text with no lowercase
word, because neither gives a case signal. The 1911 word map has no such exception.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Optional, Union

from .eras import Era, Variant
from .guard import NotPortuguese, detect_sister
from .lexicon import Lexicon, get_lexicon
from .ml import features, get_detector_model
from .rules import _MONTHS, _SEGMENT_SEP, _WORD_RE

_VOWELS = "aeiouáàâãéêíóôõúü"
_NASAL = "[mn][%s]" % _VOWELS
_RE_NASAL_PT = re.compile("[éó](?=%s)" % _NASAL)
_RE_NASAL_BR = re.compile("[êô](?=%s)" % _NASAL)
_SENTENCE_END = re.compile(r"[.!?…\n]")


@dataclass
class Orthography:
    """A detection result: which norm the text is written in."""

    era: Era
    variant: Optional[Variant] = None
    confidence: float = 0.0
    markers: List[str] = field(default_factory=list)
    note: str = ""

    @property
    def is_portuguese(self) -> bool:
        return True

    @property
    def id(self) -> str:
        # a canonical norm id that round-trips into convert()/Norm.parse(): only AO1990
        # carries a variant suffix (pt_1973 is inherently European, br_1971 Brazilian).
        if self.era == Era.AO1990 and self.variant and self.variant.value:
            return f"{self.era.value}-{self.variant.value}"
        return self.era.value

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Orthography({self.id}, confidence={self.confidence:.2f})"


def detect(
    text: str,
    lexicon: Optional[Lexicon] = None,
    method: str = "rules",
) -> Union[Orthography, NotPortuguese]:
    """Classify ``text`` as a Portuguese orthography or a sister variety.

    ``method`` chooses the classifier (the sister-language guard runs first in every
    mode, and any mode falls back to the rules if no model is bundled):

    * ``"rules"`` (default) — the deterministic marker scorer: explainable, robust on
      short inputs, and what the documented ``.id`` examples reflect;
    * ``"nb"`` — the shipped zero-dependency Naive-Bayes model;
    * ``"perceptron"`` — the shipped zero-dependency averaged-perceptron model.

    On sentence-length text the learned models score higher (~96% vs ~94% compatible
    accuracy) on held-out cross-validation — see ``benchmark/train_detector.py``. They
    are opt-in because they are less reliable on very short, marker-less inputs. Markers
    from the rule scorer are attached to a learned result for explainability.
    """
    text = unicodedata.normalize("NFC", text)
    lex = lexicon or get_lexicon()
    sister = detect_sister(text, lex)
    if sister is not None:
        return sister

    rule = _detect_rules(text, lex)
    if method == "rules":
        return rule
    model = get_detector_model("perceptron" if method == "perceptron" else "nb")
    if model is None or not features(text):
        return rule  # no model, or nothing for the model to score -> trust the rules
    col, margin = model.predict_with_margin(text)
    return _orth_from_column(col, margin, rule)


def _orth_from_column(col: str, margin: float, rule: "Orthography") -> "Orthography":
    """Build an Orthography from the model's predicted column, keeping rule markers."""
    era, variant = _COLUMN_TO_NORM.get(col, (Era.AO1990, None))
    conf = round(min(0.99, 0.5 + 0.1 * margin), 2)
    return Orthography(era=era, variant=variant, confidence=conf,
                       markers=rule.markers, note=_ERA_NOTES.get(era, ""))


_COLUMN_TO_NORM = {
    "etymological": (Era.ETYMOLOGICAL, None),
    "pt_1973": (Era.PT_1973, Variant.PT),
    "ao1990-pt": (Era.AO1990, Variant.PT),
    "br_1971": (Era.BR_1971, Variant.BR),
    "ao1990-br": (Era.AO1990, Variant.BR),
}


def _detect_rules(text: str, lex: Lexicon) -> Orthography:
    """Deterministic marker-based classifier."""
    etym = 0
    old_pt = 0
    old_br = 0
    modern = 0
    pt_lean = 0
    br_lean = 0
    markers: List[str] = []
    archaic = lex.tuga.archaic_words
    matches = list(_WORD_RE.finditer(text))
    # a text in capitals throughout gives no case signal
    cased = any(m.group().islower() for m in matches)

    for i, match in enumerate(matches):
        raw = match.group()
        w = raw.lower()
        mid_sentence = i > 0 and not _SENTENCE_END.search(
            text, matches[i - 1].end(), match.start())

        # --- pre-1911 etymological evidence -----------------------------
        if w in lex.reform1911_old2new:
            etym += 2
            markers.append(f"etym:{w}")
        elif any(seg.lower() in archaic
                 and not (cased and mid_sentence and (raw[:1].isupper() or seg[:1].isupper()))
                 for seg in _SEGMENT_SEP.split(raw)):
            # a capital part inside a sentence is a name (AO1990 Base XXI)
            etym += 1
            markers.append(f"etym-pattern:{w}")

        # --- pre-AO1990 signals the lexicon misses ----------------------
        if "êem" in w:  # lêem/crêem/vêem: -êem circumflex, dropped only by AO1990
            old_pt += 1
            markers.append(f"verbal-eem:{w}")
        if i > 0 and raw[:1].isupper() and w in _MONTHS:
            # a month capitalised mid-sentence is pre-AO1990 European (BR lowercased
            # months in 1943; AO1990 lowercased them everywhere)
            old_pt += 1
            markers.append(f"capital-month:{w}")

        # --- pre-AO1990 PT (silent consonants / dropped differentials) --
        if w in lex.ao_pt_old2new or w in lex.base_iv_drop or w in lex.differential_dropped:
            old_pt += 1
            pt_lean += 1
            markers.append(f"pre-ao90-pt:{w}")

        # --- pre-AO1990 BR (old accent/trema forms) ---------------------
        if w in lex.ao_br_old2new:
            old_br += 1
            markers.append(f"pre-ao90-br:{w}")
        if "ü" in w:
            old_br += 1
            br_lean += 1
            markers.append(f"trema:{w}")

        # --- modern AO1990 evidence -------------------------------------
        if w in lex.ao_pt_new2old or w in lex.ao_br_new2old:
            modern += 1

        # --- variant lean from PT/BR divergent spellings ----------------
        if w in lex.dual_pt2br or w in lex.divergence_pt2br:
            pt_lean += 1
            markers.append(f"pt-form:{w}")
        if w in lex.dual_br2pt or w in lex.divergence_br2pt:
            br_lean += 1
            markers.append(f"br-form:{w}")

        # --- variant lean from the nasal-vowel alternation --------------
        if _RE_NASAL_PT.search(w):
            pt_lean += 1
        if _RE_NASAL_BR.search(w):
            br_lean += 1

    old_score = old_pt + old_br
    total = etym + old_score + modern + 1e-9

    # ---- decide the era bucket ----
    if etym >= 1 and etym >= old_score and etym >= modern:
        era = Era.ETYMOLOGICAL
        variant = None
        conf = etym / total
    elif old_score > 0 and old_score >= modern:
        if old_pt >= old_br:
            era, variant = Era.PT_1973, Variant.PT
        else:
            era, variant = Era.BR_1971, Variant.BR
        conf = old_score / total
    else:
        era = Era.AO1990
        variant = _decide_variant(pt_lean, br_lean)
        conf = (modern + max(pt_lean, br_lean)) / (total + max(pt_lean, br_lean))

    # baseline confidence floor for a clean-but-featureless modern text
    if not markers and era == Era.AO1990:
        conf = 0.34

    note = _ERA_NOTES.get(era, "")
    return Orthography(
        era=era,
        variant=variant,
        confidence=round(min(0.99, max(0.0, conf)), 2),
        markers=markers,
        note=note,
    )


def _decide_variant(pt_lean: int, br_lean: int) -> Optional[Variant]:
    if pt_lean > br_lean:
        return Variant.PT
    if br_lean > pt_lean:
        return Variant.BR
    return None


_ERA_NOTES = {
    Era.ETYMOLOGICAL: "pre-1911 pseudo-etymological spelling (Greek digraphs, geminates)",
    Era.PT_1973: "pre-AO1990 European norm (silent consonants kept: óptimo, acção, facto)",
    Era.BR_1971: "pre-AO1990 Brazilian norm (trema and old accents: freqüência, idéia)",
    Era.AO1990: "AO1990 (post-1990 agreement)",
}
