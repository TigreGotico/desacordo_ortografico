import pytest

from desacordo_ortografico.eras import (
    EDGES,
    NORMS,
    Era,
    Norm,
    Variant,
    find_path,
)


class TestNormParse:
    @pytest.mark.parametrize(
        "alias,expected_id",
        [
            ("etymological", "etymological"),
            ("pre-1911", "etymological"),
            ("1911", "reforma_1911"),
            ("reforma_1911", "reforma_1911"),
            ("1943", "br_1943"),
            ("1945", "pt_1945"),
            ("ao1990-pt", "ao1990-pt"),
            ("ao1990-br", "ao1990-br"),
            ("ao90-br", "ao1990-br"),
            ("ao1990", "ao1990-pt"),
            ("pre-ao1990-pt", "pt_1973"),
            ("pre-ao1990-br", "br_1971"),
            ("brazil-pre-90", "br_1971"),
        ],
    )
    def test_aliases(self, alias, expected_id):
        assert Norm.parse(alias).id == expected_id

    def test_parse_norm_passthrough(self):
        n = NORMS["ao1990-pt"]
        assert Norm.parse(n) is n

    def test_unknown_norm_raises(self):
        with pytest.raises(ValueError):
            Norm.parse("klingon-1066")

    def test_id_only_ao1990_has_variant_suffix(self):
        assert Norm(Era.BR_1971, Variant.BR).id == "br_1971"
        assert Norm(Era.AO1990, Variant.BR).id == "ao1990-br"


class TestGraph:
    def test_all_norms_present(self):
        assert set(NORMS) == {
            "etymological", "reforma_1911", "br_1943", "pt_1945",
            "br_1971", "pt_1973", "ao1990-pt", "ao1990-br",
        }

    def test_self_path_empty(self):
        assert find_path("ao1990-pt", "ao1990-pt") == []

    def test_path_exists_between_every_pair(self):
        for a in NORMS:
            for b in NORMS:
                steps = find_path(a, b)
                assert isinstance(steps, list)

    def test_etymological_to_ao1990br_traverses_expected_edges(self):
        steps = find_path("etymological", "ao1990-br")
        edge_names = [s[0] for s in steps]
        assert edge_names[0] == "reform_1911"
        assert "br_1911_to_1943" in edge_names
        assert edge_names[-1] == "ao1990_br"

    def test_lateral_divergence_is_single_step(self):
        steps = find_path("ao1990-pt", "ao1990-br")
        assert len(steps) == 1
        assert steps[0][0] == "ptbr_divergence"

    def test_edges_reference_valid_nodes(self):
        for a, b, _name in EDGES:
            assert a in NORMS and b in NORMS
