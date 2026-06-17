"""Taxonomy of Portuguese orthographic norms and the graph that connects them.

Portuguese spelling is not a single timeline but a *(variant x era)* matrix. Two
official standards ran in parallel from 1911 until the late 2000s:

    European / PALOP line:  etymological -> 1911 -> 1945 -> 1973 -> AO1990 (PT)
    Brazilian line:         etymological -> 1911 -> 1943 -> 1971 -> AO1990 (BR)

and AO1990 itself still admits divergent European/Brazilian spellings. A conversion
is therefore a *path* through this graph of norms, applied edge by edge.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Dict, List, Tuple


class Era(str, Enum):
    """A point in the orthographic timeline."""

    ETYMOLOGICAL = "etymological"   # pre-1911 pseudo-etymological writing
    REFORMA_1911 = "reforma_1911"   # Reforma Ortografica de 1911 (Portugal)
    BR_1943 = "br_1943"             # Formulario Ortografico de 1943 (Brazil)
    PT_1945 = "pt_1945"             # Convencao Luso-Brasileira de 1945 (PT/PALOP)
    BR_1971 = "br_1971"             # Lei 5.765/1971 accent mini-reform (Brazil)
    PT_1973 = "pt_1973"             # Decreto-Lei 32/73 accent mini-reform (Portugal)
    AO1990 = "ao1990"               # Acordo Ortografico de 1990

    # rough chronological rank (parallel norms share a rank)
    @property
    def rank(self) -> int:
        return {
            "etymological": 0,
            "reforma_1911": 1,
            "br_1943": 2,
            "pt_1945": 2,
            "br_1971": 3,
            "pt_1973": 3,
            "ao1990": 4,
        }[self.value]


class Variant(str, Enum):
    """The national norm a spelling belongs to."""

    PT = "pt"          # European Portuguese (and, by default, PALOP)
    BR = "br"          # Brazilian Portuguese
    NEUTRAL = ""       # variant-agnostic node (etymological, 1911)


@dataclass(frozen=True)
class Norm:
    """A single orthographic norm: a node in the conversion graph."""

    era: Era
    variant: Variant = Variant.NEUTRAL

    @property
    def id(self) -> str:
        # Only AO1990 carries an explicit variant suffix; for the older eras the
        # national norm is already implied by the era name (br_1943, pt_1973, ...).
        if self.era == Era.AO1990 and self.variant and self.variant.value:
            return f"{self.era.value}-{self.variant.value}"
        return self.era.value

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.id

    # ------------------------------------------------------------------ parse
    _ALIASES: ClassVar[Dict[str, "Norm"]] = {}  # filled after class body

    @classmethod
    def parse(cls, value: "str | Norm") -> "Norm":
        """Resolve a norm id or human alias to a :class:`Norm`.

        Accepts canonical ids ("ao1990-pt"), years ("1911", "1990"), and friendly
        aliases ("pre-ao1990-pt", "etymological", "brazil-pre-90").
        """
        if isinstance(value, Norm):
            return value
        key = str(value).strip().lower().replace("_", "-").replace(" ", "-")
        key = key.replace("ao90", "ao1990")
        if key in _ALIASES:
            return _ALIASES[key]
        raise ValueError(
            f"Unknown orthographic norm: {value!r}. "
            f"Valid norms: {', '.join(sorted(NORMS))}"
        )


# ---------------------------------------------------------------- the norms
NORMS: Dict[str, Norm] = {
    "etymological": Norm(Era.ETYMOLOGICAL),
    "reforma_1911": Norm(Era.REFORMA_1911),
    "br_1943": Norm(Era.BR_1943, Variant.BR),
    "pt_1945": Norm(Era.PT_1945, Variant.PT),
    "br_1971": Norm(Era.BR_1971, Variant.BR),
    "pt_1973": Norm(Era.PT_1973, Variant.PT),
    "ao1990-pt": Norm(Era.AO1990, Variant.PT),
    "ao1990-br": Norm(Era.AO1990, Variant.BR),
}

# ---------------------------------------------------------------- the edges
# (older_id, newer_id, edge_name); the named transforms live in convert.py
EDGES: List[Tuple[str, str, str]] = [
    ("etymological", "reforma_1911", "reform_1911"),
    ("reforma_1911", "pt_1945", "pt_1911_to_1945"),
    ("reforma_1911", "br_1943", "br_1911_to_1943"),
    ("pt_1945", "pt_1973", "accent_1973"),
    ("br_1943", "br_1971", "accent_1971"),
    ("pt_1973", "ao1990-pt", "ao1990_pt"),
    ("br_1971", "ao1990-br", "ao1990_br"),
    ("ao1990-pt", "ao1990-br", "ptbr_divergence"),
]

# adjacency: id -> list of (neighbour_id, edge_name, forward?)
#   forward=True  means traversing a->b is the "older->newer" direction
_ADJ: Dict[str, List[Tuple[str, str, bool]]] = {nid: [] for nid in NORMS}
for _a, _b, _name in EDGES:
    _ADJ[_a].append((_b, _name, True))
    _ADJ[_b].append((_a, _name, False))


def neighbours(norm_id: str) -> List[Tuple[str, str, bool]]:
    return _ADJ[norm_id]


def find_path(src: "str | Norm", dst: "str | Norm") -> List[Tuple[str, str, bool]]:
    """Breadth-first path from ``src`` to ``dst``.

    Returns a list of ``(edge_name, from_id, forward)`` steps. ``forward`` is True
    when the step is applied in the older->newer direction for that edge.
    """
    s = Norm.parse(src)
    d = Norm.parse(dst)
    if s.id == d.id:
        return []
    # BFS
    from collections import deque

    queue = deque([s.id])
    prev: Dict[str, Tuple[str, str, bool]] = {}  # node -> (from_node, edge, forward)
    seen = {s.id}
    while queue:
        cur = queue.popleft()
        for nb, edge, forward in _ADJ[cur]:
            if nb in seen:
                continue
            seen.add(nb)
            prev[nb] = (cur, edge, forward)
            if nb == d.id:
                queue.clear()
                break
            queue.append(nb)
    if d.id not in prev:  # pragma: no cover - graph is connected
        raise ValueError(f"No conversion path from {s.id} to {d.id}")
    # reconstruct
    steps: List[Tuple[str, str, bool]] = []
    node = d.id
    while node != s.id:
        frm, edge, forward = prev[node]
        steps.append((edge, frm, forward))
        node = frm
    steps.reverse()
    return steps


# ---------------------------------------------------------------- aliases
_ALIASES = {
    # canonical ids
    **{nid: norm for nid, norm in NORMS.items()},
    **{nid.replace("_", "-"): norm for nid, norm in NORMS.items()},
    # years
    "1911": NORMS["reforma_1911"],
    "reforma-1911": NORMS["reforma_1911"],
    "1943": NORMS["br_1943"],
    "formulario-1943": NORMS["br_1943"],
    "1945": NORMS["pt_1945"],
    "convencao-1945": NORMS["pt_1945"],
    "1971": NORMS["br_1971"],
    "1973": NORMS["pt_1973"],
    "1990": NORMS["ao1990-pt"],
    "ao1990": NORMS["ao1990-pt"],
    "ao1990-pt": NORMS["ao1990-pt"],
    "ao1990-br": NORMS["ao1990-br"],
    # pre-1911 synonyms
    "pre-1911": NORMS["etymological"],
    "etimologica": NORMS["etymological"],
    "etymologic": NORMS["etymological"],
    # "pre-AO1990" == the immediate pre-reform norm of each variant
    "pre-ao1990-pt": NORMS["pt_1973"],
    "pre-ao1990-br": NORMS["br_1971"],
    "pre-ao1990": NORMS["pt_1973"],
    "portugal-pre-90": NORMS["pt_1973"],
    "brazil-pre-90": NORMS["br_1971"],
    "brasil-pre-90": NORMS["br_1971"],
}
Norm._ALIASES = _ALIASES
