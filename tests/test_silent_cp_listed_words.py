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


# Priberam, "Grafia alterada pelo Acordo Ortográfico de 1990": recto -> reto, colecta ->
# coleta, corrector -> corretor, reactivar -> reativar, inexactidão -> inexatidão, rectidão
# -> retidão (papers/linguistics/pt/priberam-cp-sweep/). Brazil writes the same forms. The
# map lists the singular of each and not the plural, so the plural rule converts it.
@pytest.mark.parametrize("target", AO)
@pytest.mark.parametrize("old, new", [
    ("rectos", "retos"), ("colectas", "coletas"), ("correctoras", "corretoras"),
    ("reactivados", "reativados"), ("inexactidões", "inexatidões"), ("rectidões", "retidões"),
    ("RECTOS", "RETOS"), ("Colectas", "Coletas"),
    ("Inexactidões", "Inexatidões"),
])
def test_the_plural_of_a_map_word_drops_the_consonant(old, new, target):
    assert old.lower() not in get_lexicon().ao_pt_old2new
    # the VOLP lists both forms of reto and coleta, so pt-BR writes the consonant:
    # "reto adj. s.m. | recto adj. s.m.", "coleta s.f. | colecta s.f."
    if target == "ao1990-br" and old.lower() in ("rectos", "colectas"):
        new = old
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
    # c/p drop, so the silent-cp feature leaves it as written; exactidões and rectas are
    # plurals of the map rows exactidão (Base IV 1º b: exato) and recta (Priberam, recta:
    # "Grafia alterada pelo Acordo Ortográfico de 1990: reta"), and the map lists neither
    assert convert("agro-químicos", "pt_1973", "ao1990-pt", features={"silent-cp"}) == "agro-químicos"
    for old, new in (("exactidões", "exatidões"), ("rectas", "retas")):
        assert old not in get_lexicon().ao_pt_old2new
        assert convert(old, "pt_1973", "ao1990-pt", features={"silent-cp"}) == new


# Priberam, post-AO1990 view: "Grafia no Brasil: infecção", "Grafia no Brasil: facção";
# "Grafia em Portugal: infeção", "Grafia em Portugal: fação"
# (papers/linguistics/pt/priberam_infeccao.html, priberam_faccao.html)
BRAZIL_KEEPS = ["infecção", "infecções", "facção", "facções"]


@pytest.mark.parametrize("target", ["ao1990-br", "br_1971"])
@pytest.mark.parametrize("word", BRAZIL_KEEPS)
def test_a_consonant_brazil_pronounces_stays_toward_pt_br(word, target):
    assert convert(f"As {word}.", "pt_1973", target) == f"As {word}."


@pytest.mark.parametrize("word", BRAZIL_KEEPS)
def test_a_consonant_brazil_pronounces_drops_toward_pt_pt(word):
    pt = word.replace("cç", "ç")
    assert convert(word, "pt_1973", "ao1990-pt") == pt
    assert convert(word, "ao1990-br", "ao1990-pt") == pt


@pytest.mark.parametrize("source", ["br_1971", "ao1990-br"])
@pytest.mark.parametrize("word", BRAZIL_KEEPS + ["recepção"])
def test_a_brazilian_consonant_form_stays_toward_older_european_norms(word, source):
    # before AO1990 the European norm wrote the consonant too (Priberam, pre-AO1990
    # view: "Grafia em Portugal: infecção")
    assert convert(word, source, "pt_1973") == word
    assert convert(word, source, "etymological") == word


# Priberam, pre-AO1990 view: "Grafia no Brasil: setorial", "Grafia no Brasil: datilógrafo",
# "Grafia no Brasil: contratura" (priberam_sectorial.html, priberam_dactilografo.html,
# priberam_contractura.html)
@pytest.mark.parametrize("source", ["pt_1973", "ao1990-pt", "etymological"])
@pytest.mark.parametrize("pt, br", [("sectorial", "setorial"), ("dactilógrafo", "datilógrafo"),
                                    ("contractura", "contratura")])
def test_a_pt_pt_dual_takes_the_brazilian_form_toward_br_1971(pt, br, source):
    assert convert(pt, source, "br_1971") == br


# Priberam: "Grafia em Portugal: secção", "Grafia no Brasil: seção" (priberam_seccao.html).
# The VOLP lists secção as a word of its own, so ao1990-br keeps it (test_volp_ao1990_br.py).
@pytest.mark.parametrize("source", ["pt_1973", "ao1990-pt"])
def test_seccao_takes_the_brazilian_form(source):
    assert convert("A secção e as secções.", source, "br_1971") == "A seção e as seções."


# the tugalex AO1990 pt-PT map has electropunctura -> eletropuntura, and eletropunctura is
# the consonant form of that dual cell: both come from electropunctura before AO1990
@pytest.mark.parametrize("target", ["pt_1973", "etymological"])
@pytest.mark.parametrize("source, word", [("ao1990-br", "eletropuntura"), ("br_1971", "eletropuntura"),
                                          ("ao1990-pt", "eletropunctura")])
def test_eletropunctura_takes_its_older_european_form(source, word, target):
    assert convert(word, source, target) == "electropunctura"


# Priberam: trato is its own entry, the noun from tratar ("maus tratos"); tracto -> trato
# is another, rarer word (a tract), so trato keeps its frequent sense
# (papers/linguistics/pt/priberam_trato.html)
@pytest.mark.parametrize("target", ["pt_1973", "etymological"])
@pytest.mark.parametrize("text", ["Sofreu maus tratos.", "Os tratos que lhe dera o marido.", "O trato."])
def test_trato_keeps_its_frequent_sense(text, target):
    assert convert(text, "ao1990-pt", target) == text
