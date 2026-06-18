"""Detect which Portuguese orthography a text is written in.

The detector is marker-based: it scans the tokens for orthographic evidence and scores
the candidate norms. Distinguishing every historical era from spelling alone is not
always possible (1911 and 1945 PT spell most words identically), so the detector
reports at the granularity that orthography actually supports: pre-1911 *etymological*,
*pre-AO1990* (PT/BR), and *AO1990* (PT/BR), with the variant left unset when no
distinguishing marker is present.

It calls the sister-language :mod:`guard` first; a :class:`~guard.NotPortuguese` result
short-circuits everything else.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Union

from .eras import Era, Variant
from .guard import NotPortuguese, detect_sister
from .lexicon import Lexicon, get_lexicon
from .rules import words as _words

_VOWELS = "aeiouáàâãéêíóôõúü"
_NASAL = "[mn][%s]" % _VOWELS
# Etymological-only patterns. Deliberately excludes mm/nn (survive in modern PT
# comummente/connosco) and sci (modern piscina/consciência); those archaic words are
# still caught by the reform1911 lexicon membership check.
_RE_ETYM = re.compile(r"ph|th|rh|(?:ll|pp|tt|bb|gg|dd|ff|cc)|[a-z]y")
_RE_NASAL_PT = re.compile("[éó](?=%s)" % _NASAL)
_RE_NASAL_BR = re.compile("[êô](?=%s)" % _NASAL)


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
        if self.variant and self.variant.value:
            return f"{self.era.value}-{self.variant.value}"
        return self.era.value

    def __str__(self) -> str:  # pragma: no cover - trivial
        v = f"-{self.variant.value}" if self.variant and self.variant.value else ""
        return f"Orthography({self.era.value}{v}, confidence={self.confidence:.2f})"


def detect(text: str, lexicon: Optional[Lexicon] = None) -> Union[Orthography, NotPortuguese]:
    """Classify ``text`` as a Portuguese orthography or a sister variety."""
    lex = lexicon or get_lexicon()

    sister = detect_sister(text, lex)
    if sister is not None:
        return sister

    etym = 0
    old_pt = 0
    old_br = 0
    modern = 0
    pt_lean = 0
    br_lean = 0
    markers: List[str] = []

    for raw in _words(text):
        w = raw.lower()

        # --- pre-1911 etymological evidence -----------------------------
        if w in lex.reform1911_old2new:
            etym += 2
            markers.append(f"etym:{w}")
        elif _RE_ETYM.search(w):
            etym += 1
            markers.append(f"etym-pattern:{w}")

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
