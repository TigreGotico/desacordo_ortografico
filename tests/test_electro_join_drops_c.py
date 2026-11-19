"""electro- joined at AO1990 pt-PT takes the form of the VOP.

The VOP (Portal da Língua Portuguesa, Vocabulário Ortográfico do Português) writes
eletroacústico, eletroíman and eletrossiderurgia without the c, and marks the form with
the c as the Brazilian variant. Lemma 144952: "eletroacústico - adjetivo ... Singular
eletroacústico eletroacústica; Plural eletroacústicos eletroacústicas ... variante AO:
electroacústico (Brasil)". Lemma 113640: "eletroíman - nome masculino ... singular
eletroíman, plural eletroímanes ... variante AO: electroíman". Lemma 48061:
"eletrossiderurgia - nome feminino ... variante AO: electrossiderurgia (Brasil)". The VOP
does not list electro-acústica, electro-íman or electro-siderurgia with a hyphen, so Base
XVI joins them, and the joined word takes the VOP form.
"""
import pytest

from desacordo_ortografico import convert


@pytest.mark.parametrize("hyphenated, joined", [
    ("electro-acústica", "eletroacústica"),
    ("electro-acústico", "eletroacústico"),
    ("electro-acústicos", "eletroacústicos"),
    ("electro-íman", "eletroíman"),
    ("electro-siderurgia", "eletrossiderurgia"),
])
def test_a_joined_electro_compound_drops_the_c_at_ao1990_pt(hyphenated, joined):
    assert convert(hyphenated, "pt_1973", "ao1990-pt") == joined


def test_the_joined_form_matches_the_solid_word():
    assert convert("electro-acústica", "pt_1973", "ao1990-pt") == convert(
        "electroacústica", "pt_1973", "ao1990-pt")
