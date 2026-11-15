"""A name inside a sentence keeps the spelling the VOLP lists for it in ao1990-br.

AO1990 Base XXI: "Para ressalva de direitos, cada qual poderá manter a escrita que, por
costume ou registo legal, adote na assinatura do seu nome. Com o mesmo fim, pode
manter-se a grafia original de quaisquer firmas comerciais, nomes de sociedades,
marcas e títulos que estejam inscritos em registo público."

Toward ao1990-br, a word that starts with a capital inside a sentence is a name. When
the ABL VOLP lists the form as written, the name stays as written through every edge.
When it does not, the name converts to the form the VOLP lists. A dual never gives a
name a c or a p that the source did not write. The first word of a sentence and text in capitals throughout
follow the rule for every other word. Each expected value comes from the VOLP entry
quoted beside it. The tests marked "guard" pass on the code before this rule too: they
hold the cases that earlier designs of the rule broke.
"""
import pytest

from desacordo_ortografico import FEATURES, convert
from desacordo_ortografico.lexicon import get_lexicon


@pytest.mark.parametrize("text, source", [
    ("e Coletivo Farra", "ao1990"),  # VOLP: coletivo adj. s.m. | colectivo adj. s.m.
    ("e Coletivo Farra", "br_1971"),
    ("Aventuras d'um Detetive Português", "ao1990"),  # VOLP: detetive s.m. | detective s.m.
    ("o Codialeto Sul", "ao1990-pt"),  # no VOLP row; tugalex dual cell codialeto, codialecto
])
def test_a_name_gains_no_consonant_from_a_dual(text, source):
    assert convert(text, source, "ao1990-br") == text


@pytest.mark.parametrize("text, source", [
    ("e Coletivo Farra", "ao1990-br"),  # guard
    ("Aventuras d'um Detetive Português", "ao1990-br"),  # guard
    ("o filme Receptores foi bom.", "pt_1973"),  # guard; VOLP: receptor (ô) adj. s.m.; no recetor
    ("o Colectivo Farra", "pt_1973"),  # guard; VOLP: coletivo adj. s.m. | colectivo adj. s.m.
    ("o Afectivo Lda", "pt_1973"),  # guard; VOLP: afetivo adj. | afectivo adj.
])
def test_a_name_the_volp_lists_stays_as_written(text, source):
    assert convert(text, source, "ao1990-br") == text


@pytest.mark.parametrize("text, source, expected", [
    # VOLP: coletivo adj. s.m. | colectivo adj. s.m. The ao1990_pt edge drops the c of
    # colectivo, and the hyphens of fim-de-semana give two more words before the name.
    ("o fim-de-semana do Coletivo Farra", "pt_1973", "o fim de semana do Coletivo Farra"),
    # VOLP: circunspeção s.f. | circunspecção s.f. The pt-PT to pt-BR edge adds the c.
    ("a Circunspeção Lda", "ao1990-pt", "a Circunspeção Lda"),
])
def test_every_edge_holds_a_name_the_volp_lists(text, source, expected):
    assert convert(text, source, "ao1990-br") == expected


def test_a_name_may_keep_a_consonant_the_source_wrote():
    """Guard. VOLP: afetivo adj. | afectivo adj. The 1911 form affectivo is no VOLP form,
    so the name converts. An edge drops the c, and the dual gives it back: the source
    wrote it, so the name gains no consonant."""
    assert convert("o Affectivo Lda", "etymological", "ao1990-br") == "o Afectivo Lda"


def test_the_1911_accent_guess_holds_a_name_the_volp_lists():
    """VOLP: eletrodo (ô) s.m. | electrodo (ô) s.m. The pt-PT form eléctrodos is no VOLP form."""
    assert convert("o Electrodos da casa", "etymological", "ao1990-br") == "o Electrodos da casa"


@pytest.mark.parametrize("text, source, expected", [
    # guard; VOLP: receptor (ô) adj. s.m.; no recetor
    ("o filme Recetores foi bom.", "ao1990-pt", "o filme Receptores foi bom."),
    # guard; VOLP: correção s.f. "ato de corrigir"; cf. correição; no correcção
    ("a Correcção Fraterna", "etymological", "a Correção Fraterna"),
    # guard; VOLP: caráter s.m.; pl. caracteres; no carácter
    ("o Carácter Nacional", "ao1990-pt", "o Caráter Nacional"),
    # guard; VOLP: acepção s.f.; no aceção
    ("a Aceção nova.", "br_1971", "a Acepção nova."),
    # guard; VOLP: projeto s.m.; no projecto
    ("o Projecto Alfa", "pt_1973", "o Projeto Alfa"),
])
def test_a_name_the_volp_does_not_list_takes_the_volp_form(text, source, expected):
    assert convert(text, source, "ao1990-br") == expected


@pytest.mark.parametrize("text, expected", [
    ("Setor público cresce.", "Sector público cresce."),  # guard
    ("o setor", "o sector"),  # guard
    ("Cresceu. Setor novo.", "Cresceu. Sector novo."),  # guard
    ("a\nSetor novo", "a\nSector novo"),  # guard
    ("O COLETIVO FARRA ABRIU.", "O COLECTIVO FARRA ABRIU."),  # guard
    ("O Coletivo Farra Abriu.", "O Colectivo Farra Abriu."),  # guard; no word in lowercase
])
def test_a_word_with_no_name_signal_takes_the_dual(text, expected):
    """VOLP: setor (ô) s.m. | sector (ô) s.m.; coletivo adj. s.m. | colectivo adj. s.m."""
    assert convert(text, "ao1990-pt", "ao1990-br") == expected


@pytest.mark.parametrize("text", [
    "Ele disse: Ótimo, vamos.",
    'Ele disse: "Ótimo, vamos."',
    "Falei com o Sr. Detetive Ótimo.",
])
def test_a_colon_a_quote_or_a_title_ends_no_sentence(text):
    """VOLP: ótimo adj. s.m. interj. | óptimo adj. s.m. interj.; detetive s.m. | detective s.m."""
    assert convert(text, "br_1971", "ao1990-br") == text


@pytest.mark.parametrize("text, source, target, features", [
    ("o Codialeto Sul", "ao1990-pt", "ao1990-br", FEATURES - {"volp"}),
    ("e Coletivo Farra", "br_1971", "ao1990-pt", FEATURES),
    ("o Electrodos da casa", "etymological", "ao1990-pt", FEATURES),
])
def test_without_the_volp_step_a_name_converts_as_a_common_word(text, source, target, features):
    """The rule reads the VOLP, so it applies toward ao1990-br with the volp feature only."""
    common = convert(text.lower(), source, target, features=features)
    assert convert(text, source, target, features=features).lower() == common


@pytest.mark.parametrize("word, listed", [
    ("setor", True),  # VOLP: setor (ô) s.m. | sector (ô) s.m.
    ("sector", True),
    ("setores", True),
    ("receptores", True),  # VOLP: receptor (ô) adj. s.m.; no recetor
    ("recetores", False),
    ("caráter", True),  # VOLP: caráter s.m.; pl. caracteres; no carácter
    ("caracteres", True),
    ("carácter", False),
    ("desinfetório", True),  # VOLP: desinfectório adj. s.m.; desinfetório s.m. is a noun only
    ("egito", True),  # VOLP: Egito top. "país da África", with no Egipto
    ("egipto", False),
    ("subsetor", False),  # Priberam subsector (Brazil after the AO1990: subsetor)
    ("abjecionista", False),  # no source: VOLP lists neither form
    ("codialeto", False),  # no VOLP row
])
def test_the_forms_the_volp_lists(word, listed):
    assert (word in get_lexicon().ao_br_volp_listed) is listed
