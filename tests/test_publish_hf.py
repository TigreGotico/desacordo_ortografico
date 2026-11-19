"""benchmark/publish_hf.py: the Hugging Face upload and the spelling datasets.

The script creates a dataset repo only when it does not exist. Each ``create_repo`` call
counts against the Hugging Face account's daily repo-creation limit, also with
``exist_ok=True`` on a repo that exists.

The spelling datasets take their spelling data from ``data/spelling.json`` of the checkout
and their lines, line order and notes from the files on the Hub. The tests give the Hub
files with ``--base``. The dry run uploads nothing. ``--upload --base DIR`` uploads the
folders of the dry run in DIR, with the Hub revision that the dry run read as the parent
commit.
"""
import csv
import fnmatch
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "benchmark" / "publish_hf.py"
TABLE = ROOT / "desacordo_ortografico" / "data" / "spelling.json"
VOLP = ROOT / "desacordo_ortografico" / "data" / "volp_ao1990_br.json"
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


#: The revision of each file on the Hub that the fixture files stand for.
PINS = {"TigreGotico/archaisms_pt": "eddede4d86525abcd8ee6b4cee87b6fb81cb55ba",
        "TigreGotico/AO1990_pt-PT": "c1695f9f07761693dd65c45ca2dba17164ae34b5",
        "TigreGotico/AO1990_pt-BR": "ebb5adc018a681a27c82fde2139ffe8d7e9db2aa"}


class StubApi:
    def __init__(self, existing, hub=None, heads=PINS):
        self.existing = existing
        self.hub = hub
        self.heads = heads
        self.calls = []

    def dataset_info(self, repo_id):
        self.calls.append(("dataset_info", repo_id))
        return types.SimpleNamespace(sha=self.heads[repo_id])

    def hf_hub_download(self, repo_id, filename, *, repo_type=None, revision=None):
        self.calls.append(("hf_hub_download", repo_id, revision))
        return str(self.hub / repo_id.split("/")[1] / filename)

    def repo_exists(self, repo_id, *, repo_type=None):
        self.calls.append(("repo_exists", repo_id, repo_type))
        return repo_id in self.existing

    def create_repo(self, repo_id, *, repo_type=None, private=None, exist_ok=False):
        self.calls.append(("create_repo", repo_id, repo_type))

    def upload_folder(self, *, repo_id, folder_path, repo_type=None, commit_message=None,
                      parent_commit=None, allow_patterns=None):
        self.calls.append(("upload_folder", repo_id, repo_type))
        self.uploaded[repo_id] = ({p.name: p.read_bytes() for p in Path(folder_path).iterdir()
                                   if allow_patterns is None
                                   or any(fnmatch.fnmatch(p.name, a) for a in allow_patterns)},
                                  parent_commit)

    uploaded: dict


def _publish(monkeypatch, existing, argv=("--repo", REPO), api=None):
    api = api or StubApi(existing)
    api.uploaded = {}
    monkeypatch.setitem(sys.modules, "huggingface_hub",
                        types.SimpleNamespace(HfApi=lambda: api, hf_hub_download=api.hf_hub_download))
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


def _write(path, rows, newline):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator=newline).writerows(rows)


#: Lines of the Hub files. Each AO1990 line is a line of the Hub file, and each archaisms line
#: is a line of the Hub file with its note.
BASE_ARCHAISMS = [
    ["threno", "treno", "", "th→t"],
    ["diphthongo", "ditongo", "", "phth→t"],
    ["hervas", "ervas", "", "h dropped"],
    ["affecto", "afeto", "", "ff→f"],
    ["pharmacia", "farmácia", "", "ph→f"],
]
BASE_PT_BR = [
    ["co-fator, co-factor", "cofator, cofactor"],
    ["cistorréia", "cistiorreia"],
    ["cistorréia", "cistorreia"],
    ["péra", "pera"],
    ["pêra", "pera"],
    ["antiictérico,antiitérico", "anti-ictérico, anti-itérico"],
    ["arqueozóico", "arqueozoico"],
    ["arqueozóico", "arqueozoico"],
    ["contra-erva", "contraerva"],
    ["dactilozóide,datilozóide", "dactilozoide, datilozoide"],
]
BASE_PT_PT = [["péra", "pera"], ["pêra", "pera"], ["accipitrino", "accipitrino, acipitrino"]]


@pytest.fixture
def base(tmp_path):
    folder = tmp_path / "base"
    for name, rows in [("archaisms_pt/archaisms.csv", BASE_ARCHAISMS),
                       ("AO1990_pt-PT/acordo_ortografico_pt_PT.csv", BASE_PT_PT),
                       ("AO1990_pt-BR/acordo_ortografico_pt_BR.csv", BASE_PT_BR)]:
        header, newline = HUB_FILES[name]
        _write(folder / name, [header, *rows], newline)
    (folder / "revisions.json").write_text(json.dumps(PINS), encoding="utf-8")
    return folder


def _dry_run(monkeypatch, base, out, extra=()):
    return _publish(monkeypatch, set(), ["--spelling", "--base", str(base), "--dry-run", str(out), *extra])


def test_spelling_dry_run_writes_the_hub_columns_and_uploads_nothing(monkeypatch, tmp_path, base):
    assert _dry_run(monkeypatch, base, tmp_path / "out") == []
    for name, (header, newline) in HUB_FILES.items():
        raw = (tmp_path / "out" / name).read_bytes().decode("utf-8")
        assert raw.count(newline) == raw.count("\n"), name
        assert _read(tmp_path / "out" / name)[0] == header, name


def test_spelling_alone_uploads_nothing(monkeypatch, tmp_path, base):
    # a complete dry run, which --upload would send
    _dry_run(monkeypatch, base, tmp_path / "out")
    api = StubApi(set())
    with pytest.raises(SystemExit):
        _publish(monkeypatch, set(), ["--spelling", "--base", str(tmp_path / "out")], api)
    assert api.calls == []


def test_spelling_dry_run_reads_the_hub_at_one_revision_and_writes_nothing(monkeypatch, tmp_path, base):
    api = StubApi(set(), hub=base)
    calls = _publish(monkeypatch, set(), ["--spelling", "--dry-run", str(tmp_path / "out")], api)
    assert calls == [c for repo, sha in PINS.items()
                     for c in [("dataset_info", repo), ("hf_hub_download", repo, sha)]]
    assert json.loads((tmp_path / "out" / "revisions.json").read_text(encoding="utf-8")) == PINS


def test_upload_needs_a_reviewed_dry_run(monkeypatch, tmp_path, base):
    api = StubApi(set(), hub=base)
    with pytest.raises(SystemExit):
        _publish(monkeypatch, set(), ["--spelling", "--upload"], api)
    assert api.calls == []


def _upload(monkeypatch, out, api):
    with pytest.raises(SystemExit):
        _publish(monkeypatch, set(), ["--spelling", "--upload", "--base", str(out)], api)


def test_upload_sends_the_dry_run_bytes_on_the_pinned_revisions(monkeypatch, tmp_path, base):
    _dry_run(monkeypatch, base, tmp_path / "out")
    # an editor backup in a reviewed folder stays on disk
    (tmp_path / "out" / "archaisms_pt" / "archaisms.csv~").write_text("stray", encoding="utf-8")
    api = StubApi(set())
    calls = _publish(monkeypatch, set(), ["--spelling", "--upload", "--base", str(tmp_path / "out")], api)
    assert calls == ([("dataset_info", repo) for repo in PINS]
                     + [("upload_folder", repo, "dataset") for repo in PINS])
    for name in HUB_FILES:
        folder, filename = (tmp_path / "out" / name).parent, (tmp_path / "out" / name).name
        repo = f"TigreGotico/{folder.name}"
        sent = {n: (folder / n).read_bytes() for n in (filename, "README.md")}
        assert api.uploaded[repo] == (sent, PINS[repo])


def test_upload_refuses_when_one_head_moved(monkeypatch, tmp_path, base):
    _dry_run(monkeypatch, base, tmp_path / "out")
    api = StubApi(set(), heads={**PINS, "TigreGotico/AO1990_pt-BR": "f" * 40})
    _upload(monkeypatch, tmp_path / "out", api)
    assert [c for c in api.calls if c[0] == "upload_folder"] == []


@pytest.mark.parametrize("revision", [None, "main", "ebb5adc", "E" * 40, PINS["TigreGotico/AO1990_pt-BR"] + "0"])
def test_upload_refuses_a_revision_that_is_no_commit_sha(monkeypatch, tmp_path, base, revision):
    _dry_run(monkeypatch, base, tmp_path / "out")
    (tmp_path / "out" / "revisions.json").write_text(
        json.dumps({**PINS, "TigreGotico/AO1990_pt-BR": revision}), encoding="utf-8")
    api = StubApi(set())
    _upload(monkeypatch, tmp_path / "out", api)
    assert api.calls == []


@pytest.mark.parametrize("name", ["AO1990_pt-BR/acordo_ortografico_pt_BR.csv", "AO1990_pt-PT/README.md"])
def test_upload_refuses_a_dry_run_without_its_csv_or_card(monkeypatch, tmp_path, base, name):
    _dry_run(monkeypatch, base, tmp_path / "out")
    (tmp_path / "out" / name).unlink()
    api = StubApi(set())
    _upload(monkeypatch, tmp_path / "out", api)
    assert api.calls == []


def test_spelling_dry_run_writes_no_revision_that_it_did_not_read(monkeypatch, tmp_path, base):
    (base / "revisions.json").unlink()
    _dry_run(monkeypatch, base, tmp_path / "out")
    assert json.loads((tmp_path / "out" / "revisions.json").read_text(encoding="utf-8")) == {}


def test_upload_refuses_a_dry_run_without_its_revisions(monkeypatch, tmp_path, base):
    _dry_run(monkeypatch, base, tmp_path / "out")
    pins = dict(PINS)
    del pins["TigreGotico/AO1990_pt-BR"]
    (tmp_path / "out" / "revisions.json").write_text(json.dumps(pins), encoding="utf-8")
    api = StubApi(set())
    with pytest.raises(SystemExit):
        _publish(monkeypatch, set(), ["--spelling", "--upload", "--base", str(tmp_path / "out")], api)
    assert api.calls == []


def test_spelling_card_gives_the_row_count_and_the_sources(monkeypatch, tmp_path, base):
    _dry_run(monkeypatch, base, tmp_path / "out")
    data = json.loads(TABLE.read_text(encoding="utf-8"))
    for name, era in [("archaisms_pt/archaisms.csv", "etymological"),
                      ("AO1990_pt-PT/acordo_ortografico_pt_PT.csv", "pt_1973"),
                      ("AO1990_pt-BR/acordo_ortografico_pt_BR.csv", "br_1971")]:
        card = (tmp_path / "out" / name).with_name("README.md").read_text(encoding="utf-8")
        rows = len(_read(tmp_path / "out" / name)) - 1
        assert f" has {rows:,} rows" in card, name
        sources = card[card.index("## Sources"):]
        listed = {line[2:] for line in sources.splitlines() if line.startswith("- ")}
        cited = {src for src in data["_sources"] if any(r["era"] == era and r["source"].startswith(src)
                                                         for r in data["rows"])}
        assert listed == cited and cited, name


@pytest.mark.parametrize("name, era", [
    ("AO1990_pt-PT/acordo_ortografico_pt_PT.csv", "pt_1973"),
    ("AO1990_pt-BR/acordo_ortografico_pt_BR.csv", "br_1971"),
])
def test_spelling_ao1990_map_is_the_table_map(monkeypatch, tmp_path, base, name, era):
    """Read as the tugalex loader documents it: each old form of a line maps to every new
    form of the line, and a later line wins."""
    _dry_run(monkeypatch, base, tmp_path / "out")
    written = {old.strip(): [n.strip() for n in new.split(",")]
               for olds, new in _read(tmp_path / "out" / name)[1:] for old in olds.split(",")}
    # pt-BR: a cell with one form takes its VOLP form, as convert() does
    volp = {r["token"]: r["form"] for r in json.loads(VOLP.read_text(encoding="utf-8"))
            if r["rows"] == "*"} if era == "br_1971" else {}
    # the VOLP has no entry for reta-pronúncia or recta-pronúncia: the pt-BR row waits for a source
    unsourced = {"recta-pronúncia"} if era == "br_1971" else set()
    cells = {r["form"]: r["value"].split("|") for r in _table(era) if r["form"] not in unsourced}
    assert written == {f: [volp.get(c[0], c[0])] if len(c) == 1 else c for f, c in cells.items()}


def test_spelling_ao1990_keeps_the_hub_lines(monkeypatch, tmp_path, base):
    _dry_run(monkeypatch, base, tmp_path / "out")
    lines = _read(tmp_path / "out" / "AO1990_pt-BR" / "acordo_ortografico_pt_BR.csv")
    hub = [line for line in lines if line in BASE_PT_BR]
    # every Hub line that the table does not change stays, in its order, once
    assert hub == [["cistorréia", "cistiorreia"], ["cistorréia", "cistorreia"], ["péra", "pera"],
                   ["pêra", "pera"], ["antiictérico,antiitérico", "anti-ictérico, anti-itérico"],
                   ["arqueozóico", "arqueozoico"], ["dactilozóide,datilozóide", "dactilozoide, datilozoide"]]
    # the table changes the forms of a line and keeps its old forms: #47, VOLP #52
    assert ["co-fator, co-factor", "cofator"] in lines
    assert ["contra-erva", "contra-erva"] in lines
    # a form that the Hub file lacks comes on a line of its own; a dual cell keeps both forms
    assert ["bissector", "bissetor, bissector"] in lines
    # the VOLP has no entry for reta-pronúncia or recta-pronúncia, so the row waits for a source
    assert "recta-pronúncia" in {r["form"] for r in _table("br_1971")}
    assert "recta-pronúncia" not in {old.strip() for olds, _new in lines for old in olds.split(",")}
    pt = _read(tmp_path / "out" / "AO1990_pt-PT" / "acordo_ortografico_pt_PT.csv")
    assert [line for line in pt if line in BASE_PT_PT] == BASE_PT_PT


def test_spelling_archaisms_keep_the_hub_order_and_notes(monkeypatch, tmp_path, base):
    _dry_run(monkeypatch, base, tmp_path / "out")
    rows = _read(tmp_path / "out" / "archaisms_pt" / "archaisms.csv")[1:]
    forms = [r[0] for r in rows]
    assert [f for f in forms if f in {b[0] for b in BASE_ARCHAISMS}] == [b[0] for b in BASE_ARCHAISMS]
    # kilo is not on the Hub; it comes after hervas, the form before it in the table
    assert forms[forms.index("hervas") + 1] == "kilo"
    by_form = {r[0]: r[1:] for r in rows}
    assert by_form["diphthongo"][2] == "phth→t"
    # VOLP: "afeto adj. s.m. | afecto adj. s.m." keeps the consonant in pt-BR
    assert by_form["affecto"] == ["afeto", "afecto", "ff→f"]
    # 1911 Base I and the AO1990 accents; the pt-BR form differs by its closed o
    assert by_form["kilometro"][:2] == ["quilómetro", "quilômetro"]
    assert by_form["architecta"][:2] == ["arquiteta", ""]
    assert all(r[3] for r in rows)
    # kermesse is the French spelling, not a pre-1911 Portuguese form
    # (knowledge/wiki/plans/desacordo-architecture-fixes.md); the table keeps its row
    assert "kermesse" in {r["form"] for r in _table("etymological")}
    assert "kermesse" not in by_form
    assert set(by_form) == {r["form"] for r in _table("etymological")} - {"kermesse"}


@pytest.mark.parametrize("name, rows, withdrawn", [
    ("archaisms_pt/archaisms.csv", BASE_ARCHAISMS, ["phlegmon", "flegmão", "", "ph→f"]),
    ("AO1990_pt-PT/acordo_ortografico_pt_PT.csv", BASE_PT_PT, ["réida", "reida"]),
    ("AO1990_pt-BR/acordo_ortografico_pt_BR.csv", BASE_PT_BR, ["aréia", "areia"]),
])
def test_spelling_drops_the_hub_line_of_a_withdrawn_form(monkeypatch, tmp_path, base, name, rows, withdrawn):
    _dry_run(monkeypatch, base, tmp_path / "without")
    header, newline = HUB_FILES[name]
    _write(base / name, [header, rows[0], withdrawn, *rows[1:]], newline)
    _dry_run(monkeypatch, base, tmp_path / "with")
    # the line goes, and every other line is written as if the Hub file never had it
    assert _read(tmp_path / "with" / name) == _read(tmp_path / "without" / name)


def test_spelling_refuses_a_hub_form_that_the_table_lacks(monkeypatch, tmp_path, base):
    _write(base / "archaisms_pt" / "archaisms.csv",
           [HUB_FILES["archaisms_pt/archaisms.csv"][0], ["phantasma-x", "fantasma-x", "", "ph→f"]], "\n")
    with pytest.raises(ValueError, match="phantasma-x"):
        _dry_run(monkeypatch, base, tmp_path / "out")


@pytest.mark.parametrize("form, notes", [
    # pre-1911 forms that the Hub file lacks: the note gives the letter changes of the pair
    ("abbade", "bb→b"),
    ("physica", "ph→f + y→i"),
    ("theoria", "th→t"),
    ("chimica", "ch→qu"),
    ("chronologia", "ch→c"),
    ("hontem", "h dropped"),
    ("damno", "mn→n"),
    ("sciencia", "silent consonant"),
    ("psalmo", "ps→s"),
    ("kilogramma", "k→qu + mm→m"),
    ("wagon", "w→v"),
    # ditongo has no f, and pronto has no t to explain alone
    ("phthysica", "phth→t + y→i"),
    ("symphonia", "symph→sinf"),
    ("prompto", "mp→n"),
    ("triumpho", "ph→f + m→n"),
    ("phlegmão", "ph→f"),
])
def test_spelling_archaisms_note_the_letter_changes(monkeypatch, tmp_path, base, form, notes):
    _dry_run(monkeypatch, base, tmp_path / "out")
    rows = {r[0]: r[3] for r in _read(tmp_path / "out" / "archaisms_pt" / "archaisms.csv")[1:]}
    assert rows[form] == notes


def _letter_changes():
    spec = importlib.util.spec_from_file_location("publish_hf", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.letter_changes


@pytest.mark.parametrize("archaic, modern, notes", [
    # ph without a new f is no ph→f
    ("joseph", "josé", "h dropped"),
    ("diphthongo", "ditongo", "phth→t"),
    ("symphonia", "sinfonia", "symph→sinf"),
    ("prompto", "pronto", "mp→n"),
    # ch before y is qu
    ("chymico", "químico", "ch→qu + y→i"),
    # fleuma has gm -> um, not gm -> m
    ("phlegma", "fleuma", "ph→f"),
    # connosco has mn -> nn, not mn -> n
    ("comnosco", "connosco", "m→n"),
])
def test_letter_changes_claim_only_what_the_pair_shows(archaic, modern, notes):
    assert _letter_changes()(archaic, modern) == notes


def test_spelling_archaisms_notes_claim_no_change_that_the_pair_lacks(monkeypatch, tmp_path, base):
    """A note that the dry run writes from the pair, for a form that neither the Hub file nor
    the tugalex note of its table row gives, writes a letter only where the modern form has
    one more of that letter."""
    _dry_run(monkeypatch, base, tmp_path / "out")
    from desacordo_ortografico.lexicon import deaccent

    noted = {b[0] for b in BASE_ARCHAISMS} | {r["form"] for r in _table("etymological")
                                              if r["source"].startswith("tugalex archaisms.csv")}
    computed = 0
    for archaic, modern, _br, notes in _read(tmp_path / "out" / "archaisms_pt" / "archaisms.csv")[1:]:
        if archaic in noted:
            continue
        computed += 1
        a, m = deaccent(archaic), deaccent(modern)
        for note in notes.split(" + "):
            written = note.split("→")[1] if "→" in note else ""
            if written and written not in note.split("→")[0]:
                assert m.count(written) > a.count(written), (archaic, modern, notes)
    assert computed > 150


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


def test_spelling_dry_run_reads_no_deprecated_tugalex_name(tmp_path, base):
    """desacordo reads tugalex defensively and drops its errors, so the bootstrap records
    each read of a deprecated name as well as warning about it."""
    result = subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-c", BOOTSTRAP,
         ",".join(DEPRECATED_TUGALEX), str(SCRIPT), "--spelling", "--base", str(base),
         "--dry-run", str(tmp_path / "out")],
        capture_output=True, text=True, check=False, env={**os.environ, "PYTHONPATH": str(ROOT)})
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-1] == "deprecated tugalex names read: []", result.stdout
    assert all((tmp_path / "out" / name).is_file() for name in HUB_FILES)


def test_spelling_refuses_a_package_that_is_not_the_checkout(tmp_path, base):
    """The table, the cards and convert() come from one checkout: a copy of the package
    elsewhere on the path stops the dry run."""
    shutil.copytree(ROOT / "desacordo_ortografico", tmp_path / "site" / "desacordo_ortografico")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--spelling", "--base", str(base), "--dry-run", str(tmp_path / "out")],
        capture_output=True, text=True, check=False,
        env={**os.environ, "PYTHONPATH": str(tmp_path / "site")})
    assert result.returncode != 0
    assert "not from this checkout" in result.stderr
    assert not (tmp_path / "out").exists()
