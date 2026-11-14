"""The silent c/p rule follows the tugalex pt-PT AO1990 map, never a guess.

AO1990 Base IV 1º: "a) Conservam-se nos casos em que são invariavelmente proferidos nas
pronúncias cultas da língua: compacto, convicção, convicto, ficção, friccionar, pacto,
pictural; adepto, apto, díptico, erupção, eucalipto, inepto, núpcias, rapto; b)
Eliminam-se nos casos em que são invariavelmente mudos nas pronúncias cultas da língua:
ação, acionar, afetivo, aflição, aflito, ato, coleção, coletivo, direção, diretor, exato,
objeção; adoção, adotar, batizar, Egito, ótimo".

A word outside the map follows the map entry of its base: its masculine singular, the
word after a prefix (autoinfecção, codialecto), or the map words that share its stem
(actores and actor). A word of the tugalex word list with no such entry stays as written,
unless it is the old form of an AO1990 map row.
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


# Priberam gives "liquefacto |áct|": pt-PT pronounces the c (data/base_iv.json keep list).
# The ao1990-pt gold cells write liquefacto. Its feminine and plurals follow it.
@pytest.mark.parametrize("word", ["liquefacto", "liquefacta", "liquefactos", "liquefactas"])
def test_pronounced_c_of_liquefacto_is_kept(word):
    assert pt(word) == word


# The forms the pt-PT map gives are valid pt-PT as written: map rows actinóide ->
# actinoide, cactóide -> cactoide, flictenóide -> flictenoide, and the dual cell
# electropunctura -> eletropuntura, eletropunctura.
@pytest.mark.parametrize("old", ["actinóide", "cactóide", "flictenóide", "electropunctura"])
def test_pt_pt_map_form_stays_as_written(old):
    form = max(TugaLexicon().ao_pt[old], key=len)
    assert pt(form) == form


# A dual cell speaks only for itself: contractura (contratura, contractura) does not keep
# the c of contractual. Priberam: contratual "Grafia em Portugal: contratual".
@pytest.mark.parametrize("src", ["pre-ao1990-pt", "etymological"])
def test_dual_is_no_evidence_for_another_word(src):
    text = "O vínculo contractual foi revisto contractualmente."
    assert convert(text, src, "ao1990-pt") == "O vínculo contratual foi revisto contratualmente."


# The word's own masculine singular row decides before a prefix base: pt-PT map row
# anticonceptivo -> anticoncetivo, while the base conceptiva is a dual cell.
@pytest.mark.parametrize("old, new", [("anticonceptiva", "anticoncetiva"),
                                      ("anticonceptivas", "anticoncetivas")])
def test_masculine_row_decides_before_a_prefix_base(old, new):
    assert pt(old) == new


# A dual base gives no evidence to a prefixed word: contracto (contracted) is a dual cell,
# subcontrato is the noun "subcontract".
def test_dual_base_is_no_evidence_for_a_prefixed_word():
    assert pt("o subcontracto") == "o subcontrato"


# codialecto follows its base dialecto -> dialeto, and its feminine and plurals follow it:
# a form the word set only generates (codialecta) is not attested as written.
@pytest.mark.parametrize("old, new", [("codialecta", "codialeta"), ("codialectas", "codialetas"),
                                      ("codialectos", "codialetos")])
def test_inflection_follows_its_prefixed_masculine(old, new):
    assert pt(old) == new


# The word list holds microelectrônica, the Brazilian accent on the pre-AO1990 letters of
# the pt-PT map row microelectrónica -> microeletrónica, so it is not valid as written and
# follows the map words of its stem.
def test_old_form_with_another_accent_is_not_attested():
    assert pt("microelectrônica") == "microeletrônica"


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


# eletro-óptica is a form of the pt-BR dual cell electroóptica, not a word of the tugalex
# word list, so pt-PT does not keep it as written: pt-PT map row óptica -> ótica.
def test_pt_br_map_form_is_not_attested_for_pt_pt():
    assert pt("eletro-óptica") == "eletro-ótica"


# The plural in -es follows its singular (Cunha & Cintra cap. 8: -es after r), so the
# plural of the pt-PT dual espectador keeps the c by the dual rule, while the map words
# of its stem drop theirs (espectáculo -> espetáculo).
def test_plural_in_es_follows_its_dual_singular():
    assert pt("os espectadores do espectaculo") == "os espectadores do espetaculo"
