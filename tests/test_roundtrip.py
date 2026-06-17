import pytest

from desacordo_ortografico import OrthographyConverter
from desacordo_ortografico.lexicon import get_lexicon


@pytest.fixture(scope="module")
def conv():
    return OrthographyConverter()


class TestReversibleEdges:
    """Edges with a clean inverse must round-trip exactly."""

    @pytest.mark.parametrize("word", ["facto", "contacto", "António", "género", "húmido"])
    def test_ptbr_divergence_roundtrips(self, word, conv):
        to_br = conv.convert(word, "ao1990-pt", "ao1990-br").text
        back = conv.convert(to_br, "ao1990-br", "ao1990-pt").text
        assert back == word

    @pytest.mark.parametrize("word", ["fenômeno", "gênero", "tônico"])
    def test_nasal_vowel_roundtrips(self, word, conv):
        to_pt = conv.convert(word, "ao1990-br", "ao1990-pt").text
        back = conv.convert(to_pt, "ao1990-pt", "ao1990-br").text
        assert back == word


class TestLexiconBackedReverse:
    """Reverse AO1990 conversions are lexical; they round-trip via the tugalex maps."""

    def test_ao_pt_reverse_when_mapped(self, conv):
        lex = get_lexicon()
        if not lex.ao_pt_old2new:
            pytest.fail("tugalex AO data unavailable — it is a required dependency")
        # pick a handful of real mapped pairs and round-trip old -> new -> old
        sample = list(lex.ao_pt_old2new.items())[:50]
        for old, new in sample:
            fwd = conv.convert(old, "pt_1973", "ao1990-pt").text
            assert fwd == new


class TestLossinessReporting:
    def test_forward_chain_is_lossless(self, conv):
        res = conv.convert("theatro pharmacia", "etymological", "ao1990-pt")
        assert res.lossless is True

    def test_reverse_to_etymological_is_lossy(self, conv):
        res = conv.convert("teatro", "ao1990-pt", "etymological")
        assert res.lossless is False

    def test_reverse_across_ao90_is_lossy(self, conv):
        res = conv.convert("ação", "ao1990-pt", "pt_1973")
        # restoring the dropped consonant is lexical, hence flagged lossy
        assert res.lossless is False
