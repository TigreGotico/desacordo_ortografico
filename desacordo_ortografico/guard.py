"""Sister-language guard.

Some languages and recognised varieties of the Iberian world look like Portuguese at
the orthographic level but are *not* Portuguese — Mirandese (a separate Astur-Leonese
language), Galician (especially in its reintegrationist spelling), and Barranquenho (a
Portuguese-Spanish contact variety). Converting them as if they were Portuguese would
mangle them, so the detector calls this guard first and, on a hit, reports a
:class:`NotPortuguese` flag instead of an orthography.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from .lexicon import Lexicon, get_lexicon
from .rules import words as _words


@dataclass
class NotPortuguese:
    """Signals that the text is a recognised non-(standard-)Portuguese variety."""

    lang: str                       # marker key, e.g. "mwl", "gl", "oki-barranquenho"
    name: str                       # human name, e.g. "Mirandese"
    confidence: float
    markers: List[str] = field(default_factory=list)
    convertible: bool = False
    status: str = ""

    @property
    def is_portuguese(self) -> bool:
        return False

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"NotPortuguese(lang={self.lang!r}, name={self.name!r}, confidence={self.confidence:.2f})"


def _match(marker: dict, text_low: str, tokens: set) -> bool:
    mtype = marker.get("type", "word")
    pat = marker["pattern"]
    if mtype == "word":
        return pat.lower() in tokens
    if mtype in ("substr", "char"):
        return pat.lower() in text_low
    if mtype == "regex":
        return re.search(pat, text_low) is not None
    return False  # pragma: no cover - unknown type


def detect_sister(text: str, lexicon: Optional[Lexicon] = None) -> Optional[NotPortuguese]:
    """Return a :class:`NotPortuguese` flag if ``text`` is a recognised sister variety.

    The best-scoring language that clears its threshold wins; ``None`` means the text is
    (or is most consistent with) Portuguese.
    """
    lex = lexicon or get_lexicon()
    text_low = text.lower()
    tokens = {w.lower() for w in _words(text)}

    best: Optional[NotPortuguese] = None
    for key, spec in lex.sister_markers.items():
        score = 0
        hits: List[str] = []
        for marker in spec.get("markers", []):
            if _match(marker, text_low, tokens):
                score += marker.get("weight", 1)
                hits.append(marker.get("note") or marker["pattern"])
        threshold = spec.get("threshold", 3)
        if score >= threshold:
            # confidence grows past the threshold, capped at 0.99
            conf = min(0.99, 0.5 + 0.1 * (score - threshold) + 0.2)
            if best is None or conf > best.confidence:
                best = NotPortuguese(
                    lang=key,
                    name=spec.get("name", key),
                    confidence=round(conf, 2),
                    markers=hits,
                    convertible=spec.get("convertible", False),
                    status=spec.get("status", ""),
                )
    return best
