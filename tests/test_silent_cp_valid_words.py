"""The silent c/p rule follows the tugalex pt-PT AO1990 map, never a guess.

AO1990 Base IV 1º: "a) Conservam-se nos casos em que são invariavelmente proferidos nas
pronúncias cultas da língua: compacto, convicção, convicto, ficção, friccionar, pacto,
pictural; adepto, apto, díptico, erupção, eucalipto, inepto, núpcias, rapto; b)
Eliminam-se nos casos em que são invariavelmente mudos nas pronúncias cultas da língua:
ação, acionar, afetivo, aflição, aflito, ato, coleção, coletivo, direção, diretor, exato,
objeção; adoção, adotar, batizar, Egito, ótimo".

A word outside the map follows the map entry of its base: the word after a prefix
(autoinfecção, codialecto), or the map words that share its stem (actores and actor). An
attested word with no such entry stays as written.
"""
import pytest
from tugalex import TugaLexicon

from desacordo_ortografico import convert
from desacordo_ortografico.lexicon import Lexicon


def pt(text):
    return convert(text, "pre-ao1990-pt", "ao1990-pt")


def test_sentence_keeps_all_three_words():
    assert pt("A aptitude do copta inapto.") == "A aptitude do copta inapto."


# Attested words (tugalex word list) with no pt-PT AO1990 map entry for themselves or a
# base. apta is the feminine of apto, raptar the verb of rapto, and políptico is formed
# like díptico (all Base IV 1º a).
KEPT = ["aptitude", "copta", "inapto", "raptar", "críptico", "políptico", "lactente",
        "secção", "dicção", "apta"]


@pytest.mark.parametrize("word", KEPT)
def test_word_without_a_map_entry_is_kept(word):
    assert word not in TugaLexicon().ao_pt
    assert pt(word) == word


# The base has a pt-PT map entry that drops the consonant (infecção -> infeção, dialecto
# -> dialeto). Priberam: autoinfeção "Grafia em Portugal: autoinfeção"; codialeto
# "Grafia alterada pelo Acordo Ortográfico de 1990: codialeto".
@pytest.mark.parametrize("old, new", [("autoinfecção", "autoinfeção"),
                                      ("codialecto", "codialeto")])
def test_prefix_word_follows_its_base(old, new):
    assert pt(old) == new


# Inflections the map does not list follow the map words of their stem: actor -> ator,
# actual -> atual, efectuar -> efetuar, detectar -> detetar.
@pytest.mark.parametrize("old, new", [("actores", "atores"), ("actuais", "atuais"),
                                      ("efectuado", "efetuado"), ("detectado", "detetado")])
def test_inflection_follows_its_stem(old, new):
    assert pt(old) == new


# The feminine and the plural of apto keep its pronounced p (Base IV 1º a: apto).
@pytest.mark.parametrize("word", ["aptas", "aptos"])
def test_inflection_of_a_kept_word_is_kept(word):
    assert pt(word) == word


# estupefacto is attested and has no pt-PT map row, so it stays; its plural follows it
# and not the map word estupefactor (estupefator) that shares its stem.
def test_plural_follows_its_singular():
    assert pt("o estupefacto e os estupefactos") == "o estupefacto e os estupefactos"


# captar keeps its p (Base IV keep list), but that says nothing of captivo, whose p is
# mute: cativo, an attested word.
def test_kept_stem_does_not_spread_to_other_words():
    assert pt("captivo") == "cativo"


def test_map_word_drops_its_consonant():
    # pt-PT map row receptor -> recetor; Priberam "Grafia em Portugal: recetor"
    assert pt("receptor") == "recetor"


# Base IV 1º b: afetivo, adotar; pt-PT map row activo -> ativo
@pytest.mark.parametrize("old, new", [("afectiva", "afetiva"), ("activos", "ativos"),
                                      ("adoptada", "adotada")])
def test_inflection_outside_the_map_still_drops(old, new):
    assert pt(old) == new


# The pt-PT map drops the c of tecto (teto, Base IV 1º b) and has no row for tectónico,
# so tectónico keeps its c. The ao1990-pt cells of gold_full.jsonl write tectónicas.
def test_short_stem_does_not_drop():
    assert pt("as placas tectónicas") == "as placas tectónicas"


# liquefacto is attested and has no pt-PT map row, so the map words of its stem
# (liquefactor -> liquefator) do not decide it. The ao1990-pt gold cells write liquefacto.
def test_attested_word_ignores_its_stem_words():
    assert pt("um gás liquefacto") == "um gás liquefacto"


def _fail(*_args, **_kwargs):
    raise RuntimeError("tugalex read failed")


def test_failed_word_list_read_raises(monkeypatch):
    monkeypatch.setattr(TugaLexicon, "get_wordlist", _fail)
    with pytest.raises(RuntimeError, match="tugalex read failed"):
        _ = Lexicon().wordset


def test_failed_map_read_raises(monkeypatch):
    monkeypatch.setattr(TugaLexicon, "__init__", _fail)
    with pytest.raises(RuntimeError, match="tugalex read failed"):
        _ = Lexicon().ao_pt_old2new
