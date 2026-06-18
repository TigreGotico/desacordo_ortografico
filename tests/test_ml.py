import pytest

from desacordo_ortografico import detect
from desacordo_ortografico.detect import Orthography
from desacordo_ortografico.guard import NotPortuguese
from desacordo_ortografico.ml import (
    LinearModel,
    features,
    get_detector_model,
    train_naive_bayes,
    train_perceptron_averaged,
)

# a tiny separable training set: digraph words vs modern words
TRAIN_X = [
    "pharmacia theatro", "philosophia chimica", "elle anno", "phosphoro lyrico",
    "farmácia teatro", "filosofia química", "ele ano", "fósforo lírico",
]
TRAIN_Y = ["old", "old", "old", "old", "new", "new", "new", "new"]


class TestFeatures:
    def test_char_ngrams_padded(self):
        f = features(" abc")
        assert "^a" in f and "c$" in f and "abc" in f

    def test_counts(self):
        f = features("aa")
        assert f["^a"] == 1 and f["a$"] == 1


@pytest.mark.parametrize("trainer", [train_naive_bayes, train_perceptron_averaged])
class TestTrainers:
    def test_learns_separable_set(self, trainer):
        m = trainer(TRAIN_X, TRAIN_Y)
        assert m.predict("pharmacia") == "old"
        assert m.predict("farmácia") == "new"

    def test_roundtrip_serialisation(self, trainer, tmp_path):
        m = trainer(TRAIN_X, TRAIN_Y)
        p = tmp_path / "m.json"
        m.save(str(p))
        m2 = LinearModel.load(str(p))
        assert m2.model_type == m.model_type
        assert m2.predict("pharmacia") == m.predict("pharmacia")

    def test_margin_nonnegative(self, trainer):
        m = trainer(TRAIN_X, TRAIN_Y)
        _, margin = m.predict_with_margin("pharmacia")
        assert margin >= 0


class TestShippedModels:
    @pytest.mark.parametrize("kind", ["nb", "perceptron"])
    def test_models_bundled(self, kind):
        assert get_detector_model(kind) is not None

    @pytest.mark.parametrize("method", ["nb", "perceptron"])
    def test_detect_method_clear_cases(self, method):
        assert detect("a pharmacia do theatro antigo", method=method).era.value == "etymological"
        r = detect("o Antônio era um génio econômico", method=method)
        assert isinstance(r, Orthography)

    @pytest.mark.parametrize("method", ["rules", "nb", "perceptron"])
    def test_guard_runs_first_in_every_method(self, method):
        assert isinstance(detect("umha cançom da naçom", method=method), NotPortuguese)

    def test_unknown_method_falls_through_to_model_or_rules(self):
        # any non-"rules"/"perceptron" string uses the NB model (or rules if absent)
        assert isinstance(detect("a ação direta", method="nb"), Orthography)
