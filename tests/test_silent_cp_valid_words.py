"""The silent c/p rule follows the tugalex pt-PT AO1990 map, never a guess.

AO1990 Base IV 1º drops the c or p where it is mute (b: "ação, acionar, afetivo, ...
adoção, adotar") and keeps it where it is pronounced (a: "adepto, apto, díptico, ...
rapto"). Where the clause allows both (c: "sector e setor"), pt-PT and pt-BR prefer
different forms, and the converter writes the form the target variety prefers.

A word outside the map follows the map entry of its base: the word after a prefix
(autoinfecção, codialecto), or the map words that share its stem (actores and actor). An
attested word with no such entry stays as written.
"""
import pytest
from tugalex import TugaLexicon

from desacordo_ortografico import convert
from desacordo_ortografico.lexicon import Lexicon

# tugalex 2.4 has no preferred form for a dual; tugalex roadmap row 1.5c adds it.
WAITS_ON_TUGALEX = pytest.mark.xfail(
    strict=True, reason="waits on the tugalex release with preferred dual forms")


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


def test_map_word_drops_its_consonant():
    # pt-PT map row receptor -> recetor; Priberam "Grafia em Portugal: recetor"
    assert pt("receptor") == "recetor"


# Base IV 1º c duals. Priberam, pt-PT: contracto "Grafia em Portugal: contracto",
# contractura "Grafia em Portugal: contractura", sectorial "Grafia em Portugal:
# sectorial".
@pytest.mark.parametrize("word", ["contracto", "contractura"])
def test_pt_pt_dual_keeps_the_preferred_form(word):
    assert pt(word) == word


def test_dual_and_its_derivative_take_the_same_form():
    assert pt("o sector sectorial") == "o sector sectorial"


@WAITS_ON_TUGALEX
def test_bissectriz_keeps_the_pt_pt_form():
    # Priberam: "Dupla grafia ...: bissetriz ou bissectriz", "Grafia em Portugal: bissectriz"
    assert pt("bissectriz") == "bissectriz"


@WAITS_ON_TUGALEX
def test_infectocontagioso_takes_the_pt_pt_form():
    # Priberam: infetocontagioso "Grafia em Portugal: infetocontagioso"
    assert pt("infectocontagioso") == "infetocontagioso"


# Base IV 1º b: afetivo, adotar; pt-PT map row activo -> ativo
@pytest.mark.parametrize("old, new", [("afectiva", "afetiva"), ("activos", "ativos"),
                                      ("adoptada", "adotada")])
def test_inflection_outside_the_map_still_drops(old, new):
    assert pt(old) == new


def _fail(*_args, **_kwargs):
    raise RuntimeError("tugalex read failed")


def test_failed_word_list_read_raises(monkeypatch):
    monkeypatch.setattr(TugaLexicon, "get_wordlist", _fail)
    with pytest.raises(RuntimeError, match="tugalex read failed"):
        Lexicon().wordset


def test_failed_preferred_form_read_raises(monkeypatch):
    monkeypatch.setattr(TugaLexicon, "modern_spelling", _fail)
    with pytest.raises(RuntimeError, match="tugalex read failed"):
        Lexicon().ao_pt_old2new


# Base IV 1º c: "sector e setor". The pt-PT map row sector -> setor, sector lists setor
# first, and setor goes back to sector.
@pytest.mark.parametrize("text", ["o setor", "o sector"])
def test_dual_form_goes_back_to_the_old_form(text):
    assert convert(text, "ao1990-pt", "pt_1973") == "o sector"


# The pt-PT map drops the c of tecto (teto, Base IV 1º b) and has no row for tectónico,
# so tectónico keeps its c. The ao1990-pt cells of gold_full.jsonl write tectónicas.
def test_short_stem_does_not_drop():
    assert pt("as placas tectónicas") == "as placas tectónicas"


# liquefacto is attested and has no pt-PT map row, so the map words of its stem
# (liquefactor -> liquefator) do not decide it. The ao1990-pt gold cells write liquefacto.
def test_attested_word_ignores_its_stem_words():
    assert pt("um gás liquefacto") == "um gás liquefacto"


# The map row contracto -> contracto, contrato lists second a word of its own: contrato
# (a contract) was spelt contrato before AO1990 too, as the pt_1973 gold cells write it.
def test_second_dual_form_that_is_a_word_does_not_go_back():
    assert convert("o contrato", "ao1990-pt", "pt_1973") == "o contrato"
