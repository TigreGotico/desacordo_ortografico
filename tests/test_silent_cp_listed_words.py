"""The silent c/p step drops a consonant only where the AO1990 word map drops it.

AO1990 Base IV 1º decides word by word, by pronunciation: "a) Conservam-se nos casos em
que são invariavelmente proferidos nas pronúncias cultas da língua: compacto, convicção,
convicto, ficção, friccionar, pacto, pictural; adepto, apto, díptico, erupção,
eucalipto, inepto, núpcias, rapto; b) Eliminam-se nos casos em que são invariavelmente
mudos nas pronúncias cultas da língua: ação, acionar, afetivo, aflição, aflito, ato,
coleção, coletivo, direção, diretor, exato, objeção; adoção, adotar, batizar, Egito,
ótimo".

So the step converts a word the tugalex AO1990 pt-PT map lists, and the regular plural
of one (actos, from the row acto -> ato). A word the map does not hold stays as written.

Priberam gives apto, inapto, aptitude and copta ("feminino singular de copto") with no
"Grafia alterada pelo Acordo Ortográfico de 1990" note, so AO1990 keeps their p
(papers/linguistics/pt/priberam_*.html). apta and aptas are the feminine of apto.
actinoide, cactoide and flictenoide are forms the AO1990 maps give, so they keep the c.
eletropunctura is the consonant form of a pt-PT dual cell (Base IV 1º c).
"""
import pytest

from desacordo_ortografico import convert
from desacordo_ortografico.lexicon import get_lexicon

AO = ("ao1990-pt", "ao1990-br")
PRONOUNCED = [
    "Ela é apta para o cargo.",
    "As candidatas são aptas.",
    "A aptitude do copta inapto.",
    "A doente é inapta para o trabalho.",
]


@pytest.mark.parametrize("target", AO)
@pytest.mark.parametrize("text", PRONOUNCED)
def test_a_pronounced_consonant_stays(text, target):
    assert convert(text, "pt_1973", target) == text


@pytest.mark.parametrize("target", AO)
@pytest.mark.parametrize("text", PRONOUNCED)
def test_a_pronounced_consonant_stays_in_capitals(text, target):
    assert convert(text.upper(), "pt_1973", target) == text.upper()


@pytest.mark.parametrize("target", AO)
def test_a_capitalised_pronounced_consonant_stays(target):
    assert convert("Apta e Copta.", "pt_1973", target) == "Apta e Copta."


@pytest.mark.parametrize("target", AO)
@pytest.mark.parametrize("word", ["actinoide", "cactoide", "flictenoide"])
def test_a_map_form_keeps_its_consonant(word, target):
    lex = get_lexicon()
    assert word in lex.ao_pt_old2new.values() and word in lex.ao_br_old2new.values()
    assert convert(word, "pt_1973", target) == word


def test_a_pt_pt_dual_keeps_its_consonant_toward_pt_pt():
    assert convert("eletropunctura", "pt_1973", "ao1990-pt") == "eletropunctura"


@pytest.mark.parametrize("target", AO)
@pytest.mark.parametrize("old, new", [
    # Base IV 1º b: ato, coletivo, ótimo, coleção, direção, objeção; the map rows acto,
    # colectivo, óptimo, colecção, direcção, objecção
    ("actos", "atos"), ("colectivos", "coletivos"), ("óptimos", "ótimos"),
    ("colecções", "coleções"), ("direcções", "direções"), ("objecções", "objeções"),
    ("Actos", "Atos"), ("COLECTIVOS", "COLETIVOS"), ("Direcções", "Direções"),
    # Base IV 1º b: acionar; the cc of the map row accionista
    ("accionistas", "acionistas"),
])
def test_the_plural_of_a_map_word_drops_the_consonant(old, new, target):
    assert convert(old, "pt_1973", target) == new


@pytest.mark.parametrize("word", ["desactiva", "detectou"])
def test_a_word_the_map_does_not_hold_stays_as_written(word):
    lex = get_lexicon()
    assert word not in lex.ao_pt_old2new
    assert convert(word, "pt_1973", "ao1990-pt") == word


@pytest.mark.parametrize("target", ["ao1990-br", "br_1971"])
@pytest.mark.parametrize("word", ["característica", "caracterizar", "telespectador"])
def test_a_pt_pt_dual_form_stays_as_written_toward_pt_br(word, target):
    # Base IV 1º c makes both forms valid ("caracteres e carateres"); the pt-PT map holds
    # both, so it drops no consonant
    assert word not in get_lexicon().ao_pt_old2new
    assert convert(word, "pt_1973", target) == word


def test_the_step_drops_only_a_consonant():
    # the plural of a map row that joins a compound (agro-químico -> agroquímico) is no
    # c/p drop, so the silent-cp feature leaves it as written
    assert convert("agro-químicos", "pt_1973", "ao1990-pt", features={"silent-cp"}) == "agro-químicos"
    assert convert("actos", "pt_1973", "ao1990-pt", features={"silent-cp"}) == "atos"
