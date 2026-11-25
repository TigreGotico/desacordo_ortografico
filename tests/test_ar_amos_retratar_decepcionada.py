"""The -ámos preterite, retratar, coletar and decepcionada.

Acordo Ortográfico de 1945, Base 17: "Assinala-se com o acento agudo, nos verbos regulares da
primeira conjugação, a terminação da primeira pessoa do plural do pretérito perfeito do
indicativo: amámos, louvámos, etc., e não amamos, louvamos, etc." AO1990 Base IX 4 keeps the
accent optional. The VOP (Portal da Língua Portuguesa) prints "adotamos / adotámos" (lemma
47917), "detetamos / detetámos" (145642) and "projetámos / projetamos" (104310).

Priberam, retratar: retratar¹ "Fazer o retrato de.", retratar² "Tornar a tratar; tratar
novamente." and the retract sense with "Grafia anterior ao Acordo Ortográfico de 1990:
retractar." The VOP has one entry for retratar (lemma 2254) and none for retractar, so the
portray sense, which was always written retratar, is the reading of a bare infinitive.

VOLP: "coletar v." and "colectar v." are two entries without "cf."; the VOP (lemma 60451)
marks colectar as Brazilian. Both forms are valid, so a form that is valid in the source stays
as written (TigreGotico/desacordo_ortografico#116).

VOP 43650: "decepcionado - adjetivo ... Brasil Masculino Feminino Singular decepcionado
decepcionada Plural decepcionados decepcionadas ... variante AO de : dececionado ( Portugal)".
"""
import pytest

from desacordo_ortografico import convert

PT = "ao1990-pt"
BR = "ao1990-br"


@pytest.mark.parametrize("old, new", [
    ("Nós adoptámos a lei.", "Nós adotámos a lei."),
    ("Detectámos o erro ontem.", "Detetámos o erro ontem."),
    ("Projectámos a ponte juntos.", "Projetámos a ponte juntos."),
    ("DECEPCIONÁMOS", "DECECIONÁMOS"),
])
def test_the_ámos_preterite_converts_like_the_other_endings(old, new):
    assert convert(old, "pt_1973", PT) == new


def test_the_present_without_the_accent_still_converts():
    assert convert("Nós adoptamos a lei.", "pt_1973", PT) == "Nós adotamos a lei."


@pytest.mark.parametrize("text", ["Nós amámos a terra.", "Louvámos o rei."])
def test_a_verb_that_no_row_holds_keeps_its_ámos_form(text):
    assert convert(text, "pt_1973", PT) == text


@pytest.mark.parametrize("target", ["pt_1973", "pt_1945", "reforma_1911", "etymological"])
def test_retratar_stays_retratar_going_back(target):
    assert convert("retratar", PT, target) == "retratar"


def test_retratar_in_a_sentence_stays_retratar_going_back():
    assert convert("Ele vai retratar a cena.", PT, "pt_1973") == "Ele vai retratar a cena."


def test_retractar_still_converts_forward():
    assert convert("Ele vai retractar a cena.", "pt_1973", PT) == "Ele vai retratar a cena."


@pytest.mark.xfail(strict=True, reason="desacordo#116: the volp step writes colectar where coletar is valid")
@pytest.mark.parametrize("source", [PT, "br_1971"])
def test_coletar_stays_coletar_toward_pt_br(source):
    assert convert("Vamos coletar os dados.", source, BR) == "Vamos coletar os dados."


@pytest.mark.parametrize("old, new", [
    ("Ela ficou decepcionada com o resultado.", "Ela ficou decepcionada com o resultado."),
    ("Elas ficaram decepcionadas.", "Elas ficaram decepcionadas."),
    ("Ele ficou decepcionado.", "Ele ficou decepcionado."),
])
def test_a_feminine_participle_keeps_the_consonant_toward_pt_br(old, new):
    assert convert(old, "pt_1973", BR) == new


@pytest.mark.parametrize("old, new", [
    ("Ela ficou decepcionada com o resultado.", "Ela ficou dececionada com o resultado."),
    ("Elas ficaram decepcionadas.", "Elas ficaram dececionadas."),
])
def test_a_feminine_participle_drops_the_consonant_toward_pt_pt(old, new):
    assert convert(old, "pt_1973", PT) == new
