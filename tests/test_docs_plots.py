"""The committed feature chart matches its drawing, and its counts name real features."""
import importlib.util
import json
from pathlib import Path

from desacordo_ortografico import FEATURES

SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "build_docs_plots.py"
spec = importlib.util.spec_from_file_location("build_docs_plots", SCRIPT)
plots = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plots)


def test_counts_name_every_feature():
    data = json.loads(plots.COUNTS.read_text(encoding="utf-8"))
    assert set(data["features"]) == FEATURES


def test_committed_svgs_match_the_counts():
    data = json.loads(plots.COUNTS.read_text(encoding="utf-8"))
    for path, svg in plots.targets(data).items():
        assert path.read_text(encoding="utf-8") == svg, path.name


def test_check_mode_exits_zero(monkeypatch):
    monkeypatch.setattr("sys.argv", ["build_docs_plots.py", "--check"])
    assert plots.main() == 0
