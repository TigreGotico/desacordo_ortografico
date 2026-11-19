"""AO1990 writes para-quedismo in pt-PT and paraquedismo in pt-BR, so a conversion
between the two varieties changes the form.

Vocabulário Ortográfico do Português (Portal da Língua Portuguesa): a search for
"paraquedismo" answers "A palavra paraquedismo não se encontra no VOP", and the forms
that start with "para-qued" are para-quedas, para-quedismo and para-quedista. ABL,
Vocabulário Ortográfico da Língua Portuguesa: "paraquedismo s.m.".
"""
import pytest

from desacordo_ortografico import convert


@pytest.mark.parametrize("word,source,target,expected", [
    ("pára-quedismo", "br_1943", "ao1990-pt", "para-quedismo"),
    ("pára-quedismo", "br_1971", "ao1990-pt", "para-quedismo"),
    ("paraquedismo", "ao1990-br", "ao1990-pt", "para-quedismo"),
    ("pára-quedismo", "pt_1945", "ao1990-br", "paraquedismo"),
    ("pára-quedismo", "pt_1973", "ao1990-br", "paraquedismo"),
    ("para-quedismo", "ao1990-pt", "ao1990-br", "paraquedismo"),
    ("Paraquedismos", "ao1990-br", "ao1990-pt", "Para-quedismos"),
    ("para-quedismos", "ao1990-pt", "ao1990-br", "paraquedismos"),
])
def test_each_variety_writes_its_form(word, source, target, expected):
    assert convert(word, source, target) == expected
