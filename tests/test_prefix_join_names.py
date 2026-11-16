"""A name keeps the hyphen of its prefix at an AO1990 target.

AO1990 Base XXI (the text of the Portal da Língua Portuguesa), "Das assinaturas e firmas":
"Para ressalva de direitos, cada qual poderá manter a escrita que, por costume ou registo
legal, adote na assinatura do seu nome. Com o mesmo fim, pode manter-se a grafia original
de quaisquer firmas comerciais, nomes de sociedades, marcas e títulos que estejam inscritos
em registo público."

Base XXI is a permission ("pode"), not a rule. The library reads it the way detect.py
does: a word inside a sentence that starts with a capital, or has a part that does, is a
name (rules.names), and it keeps the spelling it is written in. So the Base XVI join of a
prefix leaves it as written. The first word of a sentence and a text in capitals give no
case signal, so they join.
"""
import pytest

from desacordo_ortografico import convert

_ROUTES = [("pt_1973", "ao1990-pt"), ("br_1971", "ao1990-br"), ("etymological", "ao1990-pt"),
           ("etymological", "ao1990-br")]


@pytest.mark.parametrize("source,target", _ROUTES)
@pytest.mark.parametrize("text", [
    "A Co-Op Lisboa abriu.",
    "Visitei a Euro-Asia ontem.",
    "O carro da Auto-Europa chegou.",
    "A loja da Multi-Opção fechou.",
    "Comprei na Anti-Stress ontem.",
    "Falei com a co-Op ontem.",
])
def test_a_name_keeps_the_hyphen(text, source, target):
    assert convert(text, source, target) == text


@pytest.mark.parametrize("source,target", _ROUTES)
@pytest.mark.parametrize("old,new", [
    ("Co-autores do estudo.", "Coautores do estudo."),
    ("OS CO-AUTORES", "OS COAUTORES"),
    ("A Co-Op e os co-autores.", "A Co-Op e os coautores."),
])
def test_the_first_word_and_text_in_capitals_join(old, new, source, target):
    assert convert(old, source, target) == new


@pytest.mark.parametrize("source,target", _ROUTES[:2])
def test_the_name_test_follows_a_word_that_splits(source, target):
    # fim-de-semana becomes three words before the join reads the names
    text = "No fim-de-semana a Co-Op abriu e os co-autores chegaram."
    assert convert(text, source, target) == "No fim de semana a Co-Op abriu e os coautores chegaram."
