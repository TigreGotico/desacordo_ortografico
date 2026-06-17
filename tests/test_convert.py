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


class TestArchaicExpansion:
    @pytest.mark.parametrize(
        "old,new",
        [
            ("elephante", "elefante"),
            ("geographia", "geografia"),
            ("cavallo", "cavalo"),
            ("sabbado", "sábado"),
            ("damno", "dano"),
            ("psychiatria", "psiquiatria"),
            ("epitheto", "epíteto"),
            ("telegrapho", "telégrafo"),
            ("kiosque", "quiosque"),
            ("solemne", "solene"),
            ("synthese", "síntese"),
        ],
    )
    def test_etymological_to_ao1990_pt(self, old, new, conv):
        assert conv.convert(old, "etymological", "ao1990-pt").text == new

    @pytest.mark.parametrize(
        "old,br",
        [("anonymo", "anônimo"), ("kilometro", "quilômetro"), ("phenomeno", "fenômeno")],
    )
    def test_br_path_rederives_nasal(self, old, br, conv):
        # PT form is stored; the Brazilian edge must re-derive the closed nasal vowel
        assert conv.convert(old, "etymological", "ao1990-br").text == br


class TestAuditFixes:
    def test_corrupto_dual_direction(self, conv):
        # rare reversed dual: PT pronounces & keeps the p, BR may drop it
        assert conv.convert("corrupto", "ao1990-pt", "ao1990-br").text == "corruto"
        assert conv.convert("corruto", "ao1990-br", "ao1990-pt").text == "corrupto"

    def test_egypto_era_separation(self, conv):
        # 1911 simplifies y->i but KEEPS the p; only AO1990 drops it
        assert conv.convert("Egypto", "etymological", "reforma_1911").text == "Egipto"
        assert conv.convert("Egypto", "etymological", "ao1990-pt").text == "Egito"

    def test_addicao_not_adiccao(self, conv):
        assert conv.convert("addição", "etymological", "ao1990-pt").text == "adição"

    def test_br_differential_circumflex_dropped(self, conv):
        # the 1943->1971 Brazilian edge removes the differential circumflex
        assert conv.convert("êle", "br_1943", "br_1971").text == "ele"
        assert conv.convert("govêrno", "br_1943", "br_1971").text == "governo"

    def test_variant_param_selects_ao1990_subnorm(self, conv):
        # variant= must actually steer the generic 'ao1990' target to PT or BR
        assert conv.convert("o facto", "ao1990-pt", "ao1990", variant="br").text == "o fato"
        assert conv.convert("o fato", "ao1990-br", "ao1990", variant="pt").text == "o facto"


class TestConvenienceApi:
    def test_module_convert_returns_str(self):
        assert isinstance(convert("acção", "pt_1973", "ao1990-pt"), str)
        assert convert("acção", "pt_1973", "ao1990-pt") == "ação"

    def test_punctuation_and_spacing_preserved(self, conv):
        assert conv.convert("Acção, óptimo!", "pt_1973", "ao1990-pt").text == "Ação, ótimo!"
