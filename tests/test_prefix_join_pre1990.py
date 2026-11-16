"""The AO1990 prefix joins stay off the conversions between two pre-1990 norms.

The route between pt_1973 and br_1971 passes through AO1990, but both norms write the
hyphen that AO1990 Base XVI drops:

- Acordo Ortográfico de 1945 (pt_1945, pt_1973), Base XXIX: "Emprega-se o hífen em palavras
  formadas com prefixos de origem grega ou latina, ou com outros elementos análogos de
  origem grega (primitivamente adjectivos), quando convém não os aglutinar aos elementos
  imediatos, por motivo de clareza ou expressividade gráfica, por ser preciso evitar má
  leitura, ou por tal ou tal prefixo ser acentuado graficamente. Assim o documentam os
  seguintes casos: 1.°) compostos formados com os prefixos contra, extra (exceptuando-se
  extraordinário), infra, intra, supra e ultra, quando o segundo elemento tem vida à
  parte e começa por vogal, h, r ou s: contra-almirante, contra-harmónico, contra-regra,
  contra-senha; [...] 2.°) compostos formados com os elementos de origem grega auto, neo,
  proto e pseudo, quando o segundo elemento tem vida à parte e começa por vogal, h, r ou
  s: auto-educação, auto-retrato, auto-sugestão; [...] 9.°) compostos formados com o
  prefixo co, quando este tem o sentido de «a par» e o segundo elemento tem vida
  autónoma: co-autor, co-dialecto, co-herdeiro, co-proprietário".
- Formulário Ortográfico de 1943 (br_1943, br_1971), 5.º: "Nos vocábulos formados pelos
  prefixos: a) auto, contra, extra, infra, intra, neo, proto, pseudo, semi e ultra,
  quando se lhes seguem palavras começadas por vogal, h, r ou s: auto-educação,
  contra-almirante, extra-oficial, infrahepático, intra-ocular, neo-republicano,
  proto-revolucionário, pseudo-revelação, semi-selvagem, ultra-sensível, etc." The local
  copy reads "r ous" for "r ou s".

The Formulário names no co-; the br_1971 rows of the spelling table write co-autor,
co-herdeiro and co-réu with the hyphen.
"""
import pytest

from desacordo_ortografico import convert

_ROUTES = [("pt_1973", "br_1971"), ("br_1971", "pt_1973")]


@pytest.mark.parametrize("source,target", _ROUTES)
@pytest.mark.parametrize("word", [
    "co-autores", "auto-estradas", "contra-indicações", "co-réus", "co-herdeiro",
    "co-herdeiros", "auto-retratos", "Os CO-AUTORES e os Co-Réus.",
])
def test_the_hyphen_stays_between_pre_1990_norms(word, source, target):
    assert convert(word, source, target) == word


@pytest.mark.parametrize("old,new,source,target", [
    ("co-factores", "co-fatores", "pt_1973", "br_1971"),
    pytest.param("co-fatores", "co-factores", "br_1971", "pt_1973", marks=pytest.mark.xfail(
        strict=True, reason="restore_silent_cp does not restore the c of an element")),
])
def test_co_fatores_keeps_the_hyphen(old, new, source, target):
    assert convert(old, source, target) == new


@pytest.mark.parametrize("word", ["co-directores", "co-direcção", "ex-seleccionadores"])
def test_the_volp_decides_no_word_toward_pt_1973(word):
    # a pt-PT spelling at a br_1971 source keeps its consonant at the pt-PT target
    assert convert(word, "br_1971", "pt_1973") == word
