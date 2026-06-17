import pytest

from desacordo_ortografico.lexicon import get_lexicon


@pytest.fixture(scope="module")
def lex():
    return get_lexicon()


class TestBaseIV:
    @pytest.mark.parametrize("word", ["pacto", "ficção", "apto", "egípcio", "rapto"])
    def test_keep(self, word, lex):
        assert word in lex.base_iv_keep

    @pytest.mark.parametrize(
        "old,new",
        [("acção", "ação"), ("óptimo", "ótimo"), ("director", "diretor"), ("exacto", "exato")],
    )
    def test_drop(self, old, new, lex):
        assert lex.base_iv_drop[old] == new

    @pytest.mark.parametrize("pt,br", [("facto", "fato"), ("contacto", "contato"), ("receção", "recepção")])
    def test_dual(self, pt, br, lex):
        assert lex.dual_pt2br[pt] == br
        assert lex.dual_br2pt[br] == pt

    def test_keep_and_drop_are_disjoint(self, lex):
        assert not (set(lex.base_iv_keep) & set(lex.base_iv_drop))

    def test_every_dual_has_both_norms(self, lex):
        for entry in lex.base_iv_dual:
            assert entry.get("pt") and entry.get("br")


class TestDifferentialAccents:
    @pytest.mark.parametrize("old,new", [("pára", "para"), ("pêlo", "pelo"), ("pólo", "polo"), ("pêra", "pera")])
    def test_dropped(self, old, new, lex):
        assert lex.differential_dropped[old] == new

    @pytest.mark.parametrize("word", ["pôr", "pôde", "têm", "vêm"])
    def test_kept(self, word, lex):
        assert word in lex.differential_kept


class TestDivergences:
    @pytest.mark.parametrize("pt,br", [("húmido", "úmido"), ("amnistia", "anistia"), ("connosco", "conosco")])
    def test_pt2br(self, pt, br, lex):
        assert lex.divergence_pt2br[pt] == br

    def test_inverse_is_consistent(self, lex):
        for pt, br in lex.divergence_pt2br.items():
            assert lex.divergence_br2pt[br] == pt


class TestReform1911:
    @pytest.mark.parametrize(
        "old,new",
        [("elle", "ele"), ("anno", "ano"), ("chimica", "química"), ("pharmacia", "farmácia")],
    )
    def test_old2new(self, old, new, lex):
        assert lex.reform1911_old2new[old] == new

    def test_no_underscore_keys_leaked(self, lex):
        assert not any(k.startswith("_") for k in lex.reform1911_old2new)


class TestTugalexBridge:
    def test_ao_maps_present_or_empty(self, lex):
        # tugalex is the data backbone; if installed the maps are large, otherwise empty
        assert isinstance(lex.ao_pt_old2new, dict)
        assert isinstance(lex.ao_br_old2new, dict)

    def test_inverse_maps_roundtrip_keys(self, lex):
        for old, new in list(lex.ao_pt_old2new.items())[:200]:
            assert lex.ao_pt_new2old.get(new) is not None


class TestSisterMarkers:
    def test_languages_loaded(self, lex):
        assert {"mwl", "gl", "oki-barranquenho"} <= set(lex.sister_markers)

    def test_each_language_has_markers(self, lex):
        for spec in lex.sister_markers.values():
            assert spec.get("markers")
            assert spec.get("convertible") is False
