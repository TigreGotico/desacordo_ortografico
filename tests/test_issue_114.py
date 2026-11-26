"""The mute c of the acção family stays toward pt_1973; real geminates still reduce."""

import pytest

from desacordo_ortografico import convert

# In the 1945 norm the first c of acção is written in its derived words.
_KEPT = {"accionistas": "accionistas", "coleccionadores": "coleccionadores"}

_REDUCED = {
    "annullado": "anulado",
    "accelerar": "acelerar",
    "accidentalmente": "acidentalmente",
    "diccionários": "dicionários",
}


@pytest.mark.xfail(raises=AssertionError, 
    strict=True,
    reason="https://github.com/TigreGotico/desacordo_ortografico/issues/114: "
           "1911-geminates drops the mute c of accionistas")
def test_acção_family_keeps_its_mute_c():
    for word, expected in _KEPT.items():
        assert convert(word, "etymological", "pt_1973") == expected, word
    # The 1911 reform reduced these geminates (1945 Base VI 1.º, "diccionário ...
    # funccionar" among the eliminated forms). A fix that stops reducing double
    # consonants, drops c from the geminate class, or keeps any geminate before
    # ⟨i⟩ breaks them.
    for word, expected in _REDUCED.items():
        assert convert(word, "etymological", "pt_1973") == expected, word
