"""br_1971 joins a prefix that the 1943 Formulário does not list before r or s.

The Formulário Ortográfico of 1943 (Academia Brasileira de Letras):

- 45: "Só se ligam por hífen os elementos das palavras compostas em que se mantém a noção
  da composição, isto é, os elementos das palavras compostas que mantêm a sua
  independência fonética, conservando cada um a sua própria acentuação, porém formando o
  conjunto perfeita unidade de sentido."
- 46: "Dentro dêsse princípio, deve-se empregar o hífen nos seguintes casos:". Its 5.º
  names the prefixes: "a) auto, contra, extra, infra, intra, neo, proto, pseudo, semi e
  ultra, quando se lhes seguem palavras começadas por vogal, h, r ou s"; "b) ante, anti,
  arqui e sôbre, quando seguidos de palavras iniciadas por h, r ou s"; "c) supra, quando
  se lhe segue palavra encetada por vogal, r ou s". The local copy reads "r ous" and
  "porh".
- 46 3.º Observação: "Ainda que esses elementos prefixais sejam reduções de adjetivos, não
  perdem a sua individualidade morfológica, e, por isso, devem unir-se por hífen, como
  sucede com austro (=austríaco), dólico (=dolicocéfalo), euro (=europeu), telégrafo
  (=telégrafico), etc.: austro-húngaro, dólico-louro, euro-africano, telégrafo-postal,
  etc."
- 22: "Duplicam-se o r e o s todas as vezes que a um elemento de composição terminado em
  vogal se segue, sem interposição do hífen, palavra começada por uma daquelas letras:
  albirrosado, arritmia, altíssono, derrogar, prerrogativa, pressentir, ressentimento,
  sacrossanto, etc."

The Pequeno Vocabulário Ortográfico of 1943 (the OCR text in papers/linguistics/pt) writes
the unlisted prefixes solid before r and s: microssismo, microssísmico, microrradiógrafo,
microrradiografia, macrorrizo, hidrorragia, electrossiderurgia, multissecular,
plurissecular, retrosseguir, geossinclinal, telessismógrafo, fotossíntese. It writes co-
with the hyphen: co-administrador, co-arrendador, co-diretor.
"""
import pytest

from desacordo_ortografico import convert


@pytest.mark.parametrize("source", ["pt_1973", "etymological", "ao1990-br"])
@pytest.mark.parametrize("old,new", [
    ("micro-sistema", "microssistema"), ("micro-sensores", "microssensores"),
    ("Micro-Sistema", "Microssistema"), ("mini-saia", "minissaia"),
    ("hidro-sanitário", "hidrossanitário"), ("geo-referenciado", "georreferenciado"),
    ("macro-regiões", "macrorregiões"),
])
def test_an_unlisted_prefix_joins_before_r_or_s(old, new, source):
    assert convert(old, source, "br_1971") == new


@pytest.mark.parametrize("source", ["pt_1973", "etymological", "ao1990-br"])
@pytest.mark.parametrize("word", [
    # 46 5.º lists the prefix
    "auto-retrato", "anti-ruído", "contra-senha", "semi-selvagem", "supra-renal",
    # 46 3.º Observação keeps euro-, and the Vocabulário writes co- with the hyphen
    "euro-socialista", "co-seno",
    # before a vowel or h the word stays as written
    "micro-ondas", "micro-empresa", "hidro-hepático",
])
def test_the_hyphen_stays(word, source):
    assert convert(word, source, "br_1971") == word


def test_pt_1973_keeps_the_hyphen():
    # no clause of the 1945 Acordo that doubles r or s after a prefix is at hand
    assert convert("micro-sistema", "br_1971", "pt_1973") == "micro-sistema"


def test_the_join_follows_the_prefix_rs_feature():
    assert convert("micro-sistema", "pt_1973", "br_1971", features={"silent-cp"}) == "micro-sistema"
