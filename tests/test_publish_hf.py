"""benchmark/publish_hf.py: the Hugging Face upload and the spelling datasets.

The script creates a dataset repo only when it does not exist. Each ``create_repo`` call
counts against the Hugging Face account's daily repo-creation limit, also with
``exist_ok=True`` on a repo that exists.

The spelling datasets come from ``data/spelling.json`` alone, in the columns of the files
on the Hub, and the dry run uploads nothing.
"""
import csv
import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "benchmark" / "publish_hf.py"
TABLE = ROOT / "desacordo_ortografico" / "data" / "spelling.json"
REPO = "TigreGotico/desacordo_ortografico"

#: The header rows of the files on the Hub (archaisms_pt at eddede4, AO1990_pt-PT at
#: c1695f9, AO1990_pt-BR at ebb5adc), and the line ending of each file.
HUB_FILES = {
    "archaisms_pt/archaisms.csv": (["archaic", "modern", "modern_pt_BR", "notes"], "\n"),
    "AO1990_pt-PT/acordo_ortografico_pt_PT.csv": (["old_form", "new_form"], "\r\n"),
    "AO1990_pt-BR/acordo_ortografico_pt_BR.csv": (["old_form", "new_form"], "\r\n"),
}

#: The TugaLexicon names that tugalex 2.5.0a1 deprecates for the spelling table.
DEPRECATED_TUGALEX = ("archaic_words", "archaic_words_br", "modern_spelling", "ao_pt", "ao_br",
                      "AO1990", "silent_p_words", "voiced_u_words", "normalize_ao1900",
                      "reverse_ao1900_pt", "reverse_ao1900_br")


class StubApi:
    def __init__(self, existing):
        self.existing = existing
        self.calls = []

    def repo_exists(self, repo_id, *, repo_type=None):
        self.calls.append(("repo_exists", repo_id, repo_type))
        return repo_id in self.existing

    def create_repo(self, repo_id, *, repo_type=None, private=None, exist_ok=False):
        self.calls.append(("create_repo", repo_id, repo_type))

    def upload_folder(self, *, repo_id, folder_path, repo_type=None, commit_message=None):
        self.calls.append(("upload_folder", repo_id, repo_type))


def _publish(monkeypatch, existing, argv=("--repo", REPO)):
    api = StubApi(existing)
    monkeypatch.setitem(sys.modules, "huggingface_hub",
                        types.SimpleNamespace(HfApi=lambda: api))
    monkeypatch.setattr(sys, "argv", ["publish_hf.py", *argv])
    spec = importlib.util.spec_from_file_location("publish_hf", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "_load", lambda name: [])
    module.main()
    return api.calls


@pytest.mark.parametrize("existing, expected", [
    ({REPO}, [("repo_exists", REPO, "dataset"), ("upload_folder", REPO, "dataset")]),
    (set(), [("repo_exists", REPO, "dataset"), ("create_repo", REPO, "dataset"),
             ("upload_folder", REPO, "dataset")]),
], ids=["repo exists", "repo missing"])
def test_create_repo_only_for_a_missing_repo(monkeypatch, existing, expected):
    assert _publish(monkeypatch, existing) == expected


def _table(era):
    rows = json.loads(TABLE.read_text(encoding="utf-8"))["rows"]
    return [r for r in rows if r["era"] == era]


def _read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def test_spelling_dry_run_writes_the_hub_columns_and_uploads_nothing(monkeypatch, tmp_path):
    assert _publish(monkeypatch, set(), ["--spelling", "--dry-run", str(tmp_path)]) == []
    for name, (header, newline) in HUB_FILES.items():
        raw = (tmp_path / name).read_bytes().decode("utf-8")
        assert raw.count(newline) == raw.count("\n"), name
        assert _read(tmp_path / name)[0] == header, name
        assert (tmp_path / name).with_name("README.md").is_file(), name


@pytest.mark.parametrize("name, era", [
    ("AO1990_pt-PT/acordo_ortografico_pt_PT.csv", "pt_1973"),
    ("AO1990_pt-BR/acordo_ortografico_pt_BR.csv", "br_1971"),
])
def test_spelling_ao1990_rows_are_the_table_rows(monkeypatch, tmp_path, name, era):
    _publish(monkeypatch, set(), ["--spelling", "--dry-run", str(tmp_path)])
    written = [(old, new.split(", ")) for old, new in _read(tmp_path / name)[1:]]
    assert written == [(r["form"], r["value"].split("|")) for r in _table(era)]


def test_spelling_archaisms_have_one_row_per_pre1911_form(monkeypatch, tmp_path):
    _publish(monkeypatch, set(), ["--spelling", "--dry-run", str(tmp_path)])
    rows = {r[0]: r[1:] for r in _read(tmp_path / "archaisms_pt" / "archaisms.csv")[1:]}
    assert list(rows) == list(dict.fromkeys(r["form"] for r in _table("etymological")))
    # 1911 Base I and the AO1990 accents; the pt-BR form differs by its closed o
    assert rows["kilometro"][:2] == ["quilómetro", "quilômetro"]
    assert rows["caravella"] == ["caravela", "", "ll→l"]
    # a form with AO1990 rows of its own; convert() does not read them
    assert rows["architecta"] == ["arquiteta", "", "ch→qu"]
    # VOLP: "afeto adj. s.m. | afecto adj. s.m." keeps the consonant in pt-BR
    assert rows["affecto"][:2] == ["afeto", "afecto"]
    assert rows["affectado"][:2] == ["afetado", "afectado"]


BOOTSTRAP = """
import atexit, runpy, sys, warnings
import tugalex

names = set(sys.argv[1].split(","))
read = []
get = tugalex.TugaLexicon.__getattribute__

def watch(self, name):
    if name in names:
        read.append(name)
        warnings.warn(f"TugaLexicon.{name} is deprecated", DeprecationWarning, stacklevel=2)
    return get(self, name)

tugalex.TugaLexicon.__getattribute__ = watch
atexit.register(lambda: print("deprecated tugalex names read:", sorted(set(read))))
sys.argv = sys.argv[2:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


def test_spelling_dry_run_reads_no_deprecated_tugalex_name(tmp_path):
    """desacordo reads tugalex defensively and drops its errors, so the bootstrap records
    each read of a deprecated name as well as warning about it."""
    result = subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-c", BOOTSTRAP,
         ",".join(DEPRECATED_TUGALEX), str(SCRIPT), "--spelling", "--dry-run", str(tmp_path)],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-1] == "deprecated tugalex names read: []", result.stdout
    assert all((tmp_path / name).is_file() for name in HUB_FILES)
