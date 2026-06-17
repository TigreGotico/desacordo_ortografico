"""desacordo_ortografico — detect and convert between Portuguese orthographies.

A single-purpose library for the orthographic history of Portuguese: the pre-1911
etymological writing, the Reforma de 1911, the Brazilian (1943/1971) and European
(1945/1973) standards, and the Acordo Ortografico de 1990 — including the European and
Brazilian sub-variants that AO1990 keeps distinct.

    >>> from desacordo_ortografico import detect, convert
    >>> convert("pharmacia", "etymological", "ao1990-br")
    'farmácia'
    >>> detect("a pharmacia é óptima").era.value
    'etymological'

See :func:`detect` for classification and :func:`convert` (or
:class:`OrthographyConverter`) for conversion.
"""
from .convert import ConversionResult, OrthographyConverter, convert
from .detect import Orthography, detect
from .eras import EDGES, NORMS, Era, Norm, Variant, find_path
from .guard import NotPortuguese, detect_sister
from .lexicon import Lexicon, get_lexicon
from .version import VERSION_STR as __version__

__all__ = [
    "detect",
    "convert",
    "Orthography",
    "NotPortuguese",
    "detect_sister",
    "OrthographyConverter",
    "ConversionResult",
    "Era",
    "Variant",
    "Norm",
    "NORMS",
    "EDGES",
    "find_path",
    "Lexicon",
    "get_lexicon",
    "__version__",
]
