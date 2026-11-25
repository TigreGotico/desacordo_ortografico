"""The mute c of the acção family stays toward pt_1973; real geminates still reduce."""

import pytest

from desacordo_ortografico import convert

# In the 1945 norm the first c of acção is written in its derived words.
_KEPT = {"accionistas": "accionistas", "coleccionadores": "coleccionadores"}


@pytest.mark.xfail(
    strict=True,
    reason="https://github.com/TigreGotico/desacordo_ortografico/issues/114: "
           "1911-geminates drops the mute c of accionistas")
def test_acção_family_keeps_its_mute_c():
    for word, expected in _KEPT.items():
        assert convert(word, "etymological", "pt_1973") == expected, word
    # A fix that stops reducing double consonants breaks this: the 1911 reform
    # reduced annullado to anulado.
    assert convert("annullado", "etymological", "pt_1973") == "anulado"
