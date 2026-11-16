"""euro- keeps its hyphen at AO1990.

In euro-africano, euro is europeu reduced, the first element of a compound of two
adjectives. AO1990 Base XV 1: "Emprega-se o hífen nas palavras compostas por justaposição
que não contêm formas de ligação e cujos elementos, de natureza nominal, adjetival, numeral
ou verbal, constituem uma unidade sintagmática e semântica e mantêm acento próprio, podendo
dar-se o caso de o primeiro elemento estar reduzido: ano-luz, arcebispo-bispo, arco-íris,
decreto-lei, és-sueste, médico-cirurgião, rainha-cláudia, tenente-coronel, tio-avô,
turma-piloto; alcaide-mor, amor-perfeito, guarda-noturno, mato-grossense, norte-americano,
porto-alegrense, sul-africano; afro-asiático, afro-luso-brasileiro, azul-escuro,
luso-brasileiro, primeiro-ministro, primeiro-sargento, primo-infeção, segunda-feira;
conta-gotas, finca-pé, guarda-chuva."

The ABL VOLP writes euro-africano, euro-americano, euro-árabe, euro-asiático and
euro-siberiano. The VOP writes euro-africano, euro-americano, euro-asiático, euro-atlântico
and euro-austro, with their feminine forms.
"""
import pytest

from desacordo_ortografico import convert


@pytest.mark.parametrize("word", ["euro-africano", "euro-americano", "euro-árabe", "euro-asiático",
                                  "euro-siberiano"])
def test_a_volp_euro_compound_keeps_the_hyphen(word):
    assert convert(word, "br_1971", "ao1990-br") == word


@pytest.mark.parametrize("word", ["euro-africana", "euro-americano", "euro-asiática", "euro-atlântico",
                                  "euro-austro"])
def test_a_vop_euro_compound_keeps_the_hyphen(word):
    assert convert(word, "pt_1973", "ao1990-pt") == word


def test_euro_keeps_the_hyphen_in_a_sentence():
    assert convert("O comércio euro-asiático cresceu.", "pt_1973", "ao1990-pt") == \
        "O comércio euro-asiático cresceu."
