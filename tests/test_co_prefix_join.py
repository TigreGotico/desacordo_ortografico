"""The AO1990 prefix joins of Base XVI, in the singular and the plural.

AO1990 Base XVI (the text of the Portal da Língua Portuguesa):

- 1º a): "Nas formações em que o segundo elemento começa por h:
  anti-higiénico/anti-higiênico, circum-hospitalar, co-herdeiro, contra-harmónico/contra-harmônico,
  extra-humano, pré-história, sub-hepático, super-homem, ultra-hiperbólico; arqui-hipérbole,
  eletro-higrómetro, geo-história, neo-helénico/neo-helênico, pan-helenismo,
  semi-hospitalar."
- 1º b): "Nas formações em que o prefixo ou pseudoprefixo termina na mesma vogal com que se
  inicia o segundo elemento: anti-ibérico, contra-almirante, infra-axilar, supra-auricular;
  arqui-irmandade, auto-observação, eletro-ótica, micro-onda, semi-interno." Obs.: "Nas
  formações com o prefixo co-, este aglutina-se em geral com o segundo elemento mesmo
  quando iniciado por o: coobrigação, coocupante, coordenar, cooperação, cooperar, etc."
- 2º a): "Nas formações em que o prefixo ou falso prefixo termina em vogal e o segundo
  elemento começa por r ou s, devendo estas consoantes duplicar-se, prática aliás já
  generalizada em palavras deste tipo pertencentes aos domínios científico e técnico.
  Assim: antirreligioso, antissemita, contrarregra, contrassenha, cosseno, extrarregular,
  infrassom, minissaia, tal como biorritmo, biossatélite, eletrossiderurgia,
  microssistema, microrradiografia."
- 2º b): "Nas formações em que o prefixo ou pseudoprefixo termina em vogal e o segundo
  elemento começa por vogal diferente, prática esta em geral já adotada também para os
  termos técnicos e científicos. Assim: antiaéreo, coeducaçao, extraescolar,
  aeroespacial, autoestrada, autoaprendizagem, agroindustrial, hidroelétrico,
  plurianual."

Base XVI 1 sets the cases of the hyphen: "Nas formações com prefixos (como, por exemplo:
ante-, anti-, circum-, co-, contra-, entre-, extra-, hiper-, infra-, intra-, pós-, pré-,
pró-, sobre-, sub-, super-, supra-, ultra-, etc.) e em formações por recomposição, isto é,
com elementos não autónomos ou falsos prefixos, de origem grega e latina (tais como: aero-,
agro-, arqui-, auto-, bio-, eletro-, geo-, hidro-, inter-, macro-, maxi-, micro-, mini-,
multi-, neo-, pan-, pluri-, proto, pseudo, retro-, semi-, tele-, etc.), só se emprega o
hífen nos seguintes casos:". No case names co- before a consonant, so co- joins there:
co-fatores gives cofatores. The 1º b) Obs. joins co- before o: co-autores gives coautores.

The join runs once, on the words of an AO1990 target, after the VOLP and the dual cells
decide each element. Toward pt-PT each element first drops its mute c or p, as the word
alone does (co-directores -> co-diretores -> codiretores). Toward pt-BR the VOLP decides
each element (foto-recetores -> foto-receptores -> fotorreceptores). The VOLP or a dual
cell then decides the joined word as one word. The VOLP gives "cofator adj. s.m.", so
co-fatores gives co-factores by the VOLP pair fator -> factor, the join gives cofactores,
and the VOLP gives cofatores.

Before h, pt-PT keeps the hyphen of 1º a) (co-herdeiro). The ABL VOLP writes coerdeiro: a
search for "coerd" gives "coerdade s.f.", "coerdar v." and "coerdeiro s.m.", a search for
"co-herd" or "co-h" gives no row, and a search for "co-" gives only có-có, co-worker and
co-working. So pt-BR joins co- before h too, and the h goes.
"""
import pytest

from desacordo_ortografico import convert

_PT = ("pt_1973", "ao1990-pt")
_BR = ("br_1971", "ao1990-br")
_BOTH = [_PT, _BR]


@pytest.mark.parametrize("source,target", _BOTH)
@pytest.mark.parametrize("old,new", [
    # 1º b) Obs.: co- joins before o and before any other vowel
    ("co-obrigação", "coobrigação"), ("co-obrigações", "coobrigações"),
    ("co-ocupante", "coocupante"), ("co-ocupantes", "coocupantes"),
    ("co-autor", "coautor"), ("co-autores", "coautores"),
    ("co-irmão", "coirmão"), ("co-irmãos", "coirmãos"),
    # Base XVI 1: no case of the hyphen names co- before a consonant
    ("co-fator", "cofator"), ("co-fatores", "cofatores"),
    ("co-produção", "coprodução"), ("co-produções", "coproduções"),
    # 2º a)
    ("co-seno", "cosseno"), ("co-senos", "cossenos"),
    ("co-réu", "corréu"), ("co-réus", "corréus"),
])
def test_co_joins_in_both_varieties(old, new, source, target):
    assert convert(old, source, target) == new


@pytest.mark.parametrize("source,target", _BOTH)
@pytest.mark.parametrize("old,new", [
    ("Co-Autores", "Coautores"),
    ("Co-autores", "Coautores"),
    ("CO-AUTORES", "COAUTORES"),
    ("Os co-autores e os CO-FATORES.", "Os coautores e os COFATORES."),
])
def test_capitals(old, new, source, target):
    assert convert(old, source, target) == new


def test_the_volp_pair_of_fator_does_not_reach_the_compound():
    # VOLP: cofator adj. s.m.
    assert convert("os co-fatores", *_BR) == "os cofatores"


@pytest.mark.parametrize("old", ["co-factor", "co-factores"])
def test_pt_pt_co_factor_joins_and_drops_the_c(old):
    # the map: cofactor -> cofator, cofactores -> cofatores
    assert convert(old, *_PT) == old.replace("-", "").replace("ct", "t")


@pytest.mark.parametrize("old", ["co-herdeiro", "co-herdeiros"])
def test_co_before_h(old):
    assert convert(old, *_PT) == old
    assert convert(old, *_BR) == old.replace("-h", "")


@pytest.mark.parametrize("source,target", _BOTH)
@pytest.mark.parametrize("old,new", [
    # 2º b): a different vowel joins
    ("auto-estrada", "autoestrada"), ("auto-estradas", "autoestradas"),
    ("extra-escolar", "extraescolar"), ("extra-escolares", "extraescolares"),
    ("anti-aéreo", "antiaéreo"), ("anti-aéreos", "antiaéreos"),
    ("contra-indicação", "contraindicação"), ("contra-indicações", "contraindicações"),
    ("infra-estrutura", "infraestrutura"), ("infra-estruturas", "infraestruturas"),
    # 2º a): r and s double
    ("contra-senhas", "contrassenhas"), ("anti-semitas", "antissemitas"),
    ("auto-retratos", "autorretratos"),
])
def test_other_prefixes_join(old, new, source, target):
    assert convert(old, source, target) == new


@pytest.mark.parametrize("source,target", _BOTH)
@pytest.mark.parametrize("word", [
    # 1º b): the same vowel keeps the hyphen
    "anti-ibérico", "contra-almirante", "contra-almirantes", "supra-auricular",
    "auto-observação", "micro-onda", "micro-ondas", "semi-interno",
    # 1º a): h keeps the hyphen
    "contra-harmónico", "anti-higiénico", "semi-hospitalar",
    # no prefix
    "guarda-sol",
])
def test_the_hyphen_stays(word, source, target):
    assert convert(word, source, target) == word


@pytest.mark.parametrize("old,new", [
    # the rows co-director -> codiretor and director -> diretor
    ("co-directores", "codiretores"), ("co-directoras", "codiretoras"),
    ("Co-Directores", "Codiretores"),
    ("co-redactores", "corredatores"), ("co-dialectos", "codialetos"),
    ("co-direcções", "codireções"), ("auto-infecções", "autoinfeções"),
    # Base IV 1º b drops the mute c of each element, also where no prefix joins
    ("directores-gerais", "diretores-gerais"),
    ("sector-chave", "sector-chave"),
])
def test_pt_pt_drops_the_mute_c_of_each_element(old, new):
    assert convert(old, *_PT) == new


@pytest.mark.parametrize("old,new", [
    # VOLP: director -> diretor, redactor -> redator, direcção -> direção
    ("O co-director chegou.", "O codiretor chegou."),
    ("co-redactores", "corredatores"), ("co-direcção", "codireção"),
    ("Co-Director", "Codiretor"),
])
def test_pt_br_drops_the_mute_c_of_each_element_before_the_join(old, new):
    assert convert(old, "etymological", "ao1990-br") == new
    assert convert(old, "br_1971", "ao1990-br") == new


@pytest.mark.parametrize("source,target", _BOTH)
@pytest.mark.parametrize("word", [
    # VOLP, Vocabulário de Estrangeirismos: "co-worker s.2g. ing.", "co-working s.m. ing."
    "co-working", "co-worker", "Co-Working", "anti-aging",
    # no letter after the hyphen
    "co-1, co-2 e co-3", "co-1a",
])
def test_no_join_for_a_loanword_or_a_digit(word, source, target):
    assert convert(word, source, target) == word


@pytest.mark.parametrize("old,new", [
    # VOLP: receptor, ruptura and infecção keep the consonant in pt-BR
    ("foto-receptores", "fotorreceptores"), ("tele-receptores", "telerreceptores"),
    ("contra-rupturas", "contrarrupturas"), ("auto-infecções", "autoinfecções"),
    # VOLP: director -> diretor; "cofator adj. s.m."
    ("co-directores", "codiretores"), ("co-fatores", "cofatores"), ("co-factores", "cofatores"),
])
def test_pt_pt_text_toward_pt_br_keeps_what_the_volp_writes(old, new):
    assert convert(old, "pt_1973", "ao1990-br") == new


@pytest.mark.parametrize("word", ["foto-receptores", "tele-receptores", "contra-rupturas", "auto-infecções"])
def test_pt_pt_text_toward_br_1971_keeps_the_consonant_and_the_hyphen(word):
    assert convert(word, "pt_1973", "br_1971") == word


@pytest.mark.parametrize("old,new", [
    ("co-directores", "codiretores"), ("co-autores", "coautores"), ("auto-retratos", "autorretratos"),
    ("foto-receptores", "fotorrecetores"),
])
def test_pt_pt_text_toward_pt_pt(old, new):
    assert convert(old, "pt_1973", "ao1990-pt") == new


def test_the_join_follows_the_prefix_rs_feature():
    assert convert("co-autores", "pt_1973", "ao1990-pt", features={"silent-cp"}) == "co-autores"
    assert convert("co-autores", "pt_1973", "ao1990-pt", features={"prefix-rs"}) == "coautores"


@pytest.mark.parametrize("old,new", [("co-dialecto", "codialecto"), ("co-dialectos", "codialectos")])
def test_a_dual_cell_decides_the_joined_word_in_both_numbers(old, new):
    # tugalex holds the pt-BR dual codialeto | codialecto, and Base IV 1º c writes the c
    assert convert(old, "br_1971", "ao1990-br") == new


@pytest.mark.parametrize("old,new", [("peixe-eléctrico", "peixe-elétrico"), ("peixe-eléctricos", "peixe-elétricos")])
def test_the_volp_drops_a_compound_it_holds_whole_in_both_numbers(old, new):
    assert convert(old, "br_1971", "ao1990-br") == new
