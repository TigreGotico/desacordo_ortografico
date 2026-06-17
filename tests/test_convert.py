import pytest

from desacordo_ortografico import OrthographyConverter, convert


@pytest.fixture(scope="module")
def conv():
    return OrthographyConverter()


class TestForwardConversions:
    @pytest.mark.parametrize(
        "text,src,dst,expected",
        [
            # 1911 digraph reform
            ("theatro", "etymological", "reforma_1911", "teatro"),
            ("pharmacia", "etymological", "reforma_1911", "farmácia"),
            ("pharmacia e theatro", "etymological", "ao1990-pt", "farmácia e teatro"),
            # AO1990 PT (silent consonants + accents)
            ("acção", "pt_1973", "ao1990-pt", "ação"),
            ("óptimo", "pt_1973", "ao1990-pt", "ótimo"),
            ("director", "pt_1973", "ao1990-pt", "diretor"),
            ("acção directa", "pt_1973", "ao1990-pt", "ação direta"),
            ("anti-religioso", "pt_1973", "ao1990-pt", "antirreligioso"),
            # AO1990 BR (accents + trema)
            ("idéia", "br_1971", "ao1990-br", "ideia"),
            ("vôo", "br_1971", "ao1990-br", "voo"),
            ("freqüência", "br_1971", "ao1990-br", "frequência"),
            ("lêem", "br_1971", "ao1990-br", "leem"),
        ],
    )
    def test_forward(self, text, src, dst, expected, conv):
        assert conv.convert(text, src, dst).text == expected


class TestVariantDivergence:
    @pytest.mark.parametrize(
        "text,expected",
        [("facto", "fato"), ("contacto", "contato"), ("António", "Antônio"), ("género", "gênero")],
    )
    def test_pt_to_br(self, text, expected, conv):
        assert conv.convert(text, "ao1990-pt", "ao1990-br").text == expected

    @pytest.mark.parametrize(
        "text,expected",
        [("fato", "facto"), ("Antônio", "António"), ("gênero", "género")],
    )
    def test_br_to_pt(self, text, expected, conv):
        assert conv.convert(text, "ao1990-br", "ao1990-pt").text == expected

    def test_case_preserved(self, conv):
        assert conv.convert("ANTÓNIO", "ao1990-pt", "ao1990-br").text == "ANTÔNIO"


class TestPermittedSpellings:
    def test_dual_returns_both(self, conv):
        assert set(conv.permitted_spellings("facto", "ao1990-pt")) == {"facto", "fato"}

    def test_unambiguous_returns_single(self, conv):
        assert conv.permitted_spellings("casa", "ao1990-pt") == ["casa"]

    def test_divergence_returns_both(self, conv):
        assert set(conv.permitted_spellings("antónio", "ao1990-pt")) == {"antónio", "antônio"}


class TestResultMetadata:
    def test_alternatives_collected(self, conv):
        res = conv.convert("o facto é húmido", "ao1990-pt", "ao1990-br")
        assert "facto" in res.alternatives

    def test_backward_to_etymological_is_lossy(self, conv):
        res = conv.convert("farmácia", "ao1990-pt", "etymological")
        assert res.lossless is False
        assert res.warnings

    def test_forward_is_lossless_flagged(self, conv):
        res = conv.convert("theatro", "etymological", "ao1990-pt")
        assert res.lossless is True
        assert res.warnings == []

    def test_unknown_words_pass_through(self, conv):
        assert conv.convert("xilofone azul", "pt_1973", "ao1990-pt").text == "xilofone azul"


class TestConvenienceApi:
    def test_module_convert_returns_str(self):
        assert isinstance(convert("acção", "pt_1973", "ao1990-pt"), str)
        assert convert("acção", "pt_1973", "ao1990-pt") == "ação"

    def test_punctuation_and_spacing_preserved(self, conv):
        assert conv.convert("Acção, óptimo!", "pt_1973", "ao1990-pt").text == "Ação, ótimo!"
