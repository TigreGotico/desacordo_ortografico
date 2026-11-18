"""The plural of a VOLP row follows its singular when the quote notes the plural vowel.

A VOLP quote such as "afetuoso (ô) adj.; f. (ó); pl. (ó)" gives the open vowel of the
feminine and of the plural. It names no plural form, so the regular plural of the row
takes the form of the row, as the singular does. A quote that names a plural ("caráter
s.m.; pl. caracteres") still gives no derived plural.
"""
import pytest

from desacordo_ortografico import convert

SOURCES = ("br_1971", "pt_1973", "ao1990-pt")


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("plural, expected", [
    # VOLP: afetuoso (ô) adj.; f. (ó); pl. (ó) | afectuoso (ô) adj.; f. (ó); pl. (ó)
    ("afetuosos", "afectuosos"),
    # VOLP: defectuoso (ô) adj.; f. (ó); pl. (ó); no defetuoso
    ("defetuosos", "defectuosos"),
    # VOLP: espetaculoso (ô) adj.; f. (ó); pl. (ó); no espectaculoso
    ("espectaculosos", "espetaculosos"),
    # VOLP: efetuoso (ô) adj.; f. (ó); pl. (ó); no efectuoso
    ("efectuosos", "efetuosos"),
])
def test_the_plural_takes_the_volp_form(plural, expected, source):
    assert convert(f"os {plural}", source, "ao1990-br") == f"os {expected}"


@pytest.mark.parametrize("source", SOURCES)
def test_a_named_plural_is_not_derived(source):
    # VOLP: caráter s.m.; pl. caracteres
    assert convert("os caracteres", source, "ao1990-br") == "os caracteres"
