"""The plural of a Base IV dual converts between pt-PT and pt-BR like its singular.

AO1990 Base IV 1º c lists the duals "aspecto e aspeto, ... facto e fato, ... recepção e
receção". The converter maps the singulars; a regular plural (-s, -ão to -ões) takes the
plural of the mapped form.
"""
import pytest

from desacordo_ortografico import convert


@pytest.mark.parametrize("pt, br", [("aspetos", "aspectos"), ("receções", "recepções")])
def test_plural_converts_both_ways(pt, br):
    assert convert(f"os {pt}", "ao1990-pt", "ao1990-br") == f"os {br}"
    assert convert(f"os {br}", "ao1990-br", "ao1990-pt") == f"os {pt}"


def test_singular_still_converts():
    assert convert("o aspeto", "ao1990-pt", "ao1990-br") == "o aspecto"
