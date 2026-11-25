# desacordo_ortografico: agent guide

<!-- agent-hint
covers: how to set up, test and change the repository, and the rules the code and tests enforce
source: `pyproject.toml`, `tests/test_spelling_table.py`, `desacordo_ortografico/lexicon.py`
generated: no
verify: grep -v '^verify:' AGENTS.md | grep -o '](\([^)#]*\)' | sed 's/](//' | grep -v '^http' | while read f; do test -e "$f" || exit 1; done
see: `docs/index.md`, `README.md`
-->

`desacordo_ortografico` is a Python package that converts Portuguese text between eight spelling norms and detects which norm a text follows. It does only that, with rules and cited word tables, and it depends on `tugalex` for the word list.

The documentation starts at [docs/index.md](docs/index.md).

## Repository map

| Path | Holds |
|---|---|
| `desacordo_ortografico/convert.py`, `rules.py`, `eras.py` | The conversion graph, its feature steps and the rules ([api.md](docs/api.md), [features.md](docs/features.md)) |
| `desacordo_ortografico/detect.py`, `guard.py`, `ml.py` | Detection, the sister-language guard and the learned models |
| `desacordo_ortografico/lexicon.py`, `data/*.json` | The loader and every data file ([data.md](docs/data.md)) |
| `desacordo_ortografico/cli.py` | The `desacordo` command |
| `tests/`, `examples/` | The test suite and five usage scripts |
| `benchmark/`, `tools/` | The silver corpus, scoring scripts and data-building scripts ([benchmark](benchmark/README.md), [tools](tools/README.md)) |
| `docs/` | The documentation: six pages and the `assets/` folder of the feature chart ([index](docs/index.md)) |
| `tools/build_docs_plots.py` | Counts the words each feature changes and draws the chart of [features.md](docs/features.md) |

## Setup and tests

```bash
unset VIRTUAL_ENV
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python --prerelease=allow -e '.[test]'
.venv/bin/python -m pytest tests
```

Use uv, never pip. The `benchmark` extra adds `matplotlib` for the plot script. Each `verify` command calls `python`, so run `source .venv/bin/activate` first.

## Hard rules

1. Every row of `data/spelling.json` names its edge and its source, and its `curated` flag is a boolean. A test enforces both ([data.md](docs/data.md)).
2. Data files are JSON, and the wheel ships `data/*.json` ([data.md](docs/data.md#files-in-the-wheel)).
3. Each rule file lists its `_sources`, and each word row of the spelling table cites its source. A VOLP row with no source says so ([orthographies.md](docs/orthographies.md)).
4. `convert()` reads the spelling table, not the tugalex lists. `tugalex` supplies the word list, and its floor is `>=2.4.9a1` in `pyproject.toml`.
5. The package supports Python 3.11 and later.
6. Mirandese, Galician and Barranquenho are flagged, never converted: `guard.py` returns a `NotPortuguese` flag for them ([quickstart.md](docs/quickstart.md)).
7. An edge that drops a silent consonant or an accent is lossy, and its `reversible_forward` or `reversible_backward` flag says so (`convert.py`).
8. Issue #107 lists conversions of -ar verb forms that are wrong. Documentation never presents them as working ([api.md](docs/api.md#known-limits)).

## Before you push

1. Run the full test suite.
2. If you changed a page, run its `verify` command from the `agent-hint` comment after its H1.
3. A page you add goes in the table of `docs/index.md` and gets an `agent-hint` comment and a footer whose Home link points to the index.
4. If you change a feature or a spelling table, run `python tools/build_docs_plots.py --count`, then `--write`, to redraw the chart. `tests/test_docs_plots.py` fails when a committed SVG differs from its drawing.

---
[Home](docs/index.md)
