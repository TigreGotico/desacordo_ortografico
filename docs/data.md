# Data files and datasets

<!-- agent-hint
covers: which JSON data file holds which rule or word table, how each row cites its source, and how the Hugging Face datasets are built
source: `desacordo_ortografico/data/*.json`, `desacordo_ortografico/lexicon.py`, `benchmark/publish_hf.py`, `tools/build_spelling_table.py`
generated: no
verify: diff <(ls desacordo_ortografico/data | LC_ALL=C sort) <(grep -o '^| `[a-z0-9_]*\.json`' docs/data.md | tr -d '|` ' | LC_ALL=C sort) && d=$(mktemp -d) && sed '/^```/d' docs/data.md > $d/x.txt && python -I -m doctest $d/x.txt
see: `api.md`, `orthographies.md`, `index.md`
-->

This page lists the data files that ship in the wheel, says what each one holds, and describes the Hugging Face datasets that the repository builds from them. Every data file is JSON. Each rule file carries an `_about` note and a `_sources` list, and the word tables cite a source per row.

## Files in the wheel

| File | Holds |
|---|---|
| `spelling.json` | The spelling table: 12,431 rows. Each row has `form`, `era`, `target`, `value`, `curated` and `source`. It holds the AO1990 word maps, the pre-1911 archaisms, and the 1911 words that no rule reaches (`quási` gives `quase`, `cena` gives `scena` backward). Each row of the 1911 words quotes its clause. The tugalex word lists are the source of the AO1990 and archaism rows. |
| `volp_ao1990_br.json` | 1,821 pt-BR spelling decisions. Each row cites its source: 1,653 quote the ABL *Vocabulário Ortográfico da Língua Portuguesa* (VOLP), 66 cite Priberam, and 102 record that no source decides the word. |
| `base_iv.json` | The AO1990 Base IV classification of consonant sequences: the keep, drop and dual lists. |
| `differential_accents.json` | The differential accents that the AO1990 drops and keeps, and the accents that return backward. |
| `accent_reform_1971_73.json` | The differential circumflex list of the 1971 and 1973 mini-reforms, and the kept forms. |
| `lexicalized_hyphens.json` | The compounds that AO1990 Base XV 1º Obs. joins into one word. |
| `hyphen_loanwords.json` | The hyphenated loanwords that the VOLP (pt-BR) and the *Vocabulário Ortográfico do Português* (VOP, pt-PT) mark as foreign. The prefix join leaves the rows of each variety as written: `mini-system` stays at ao1990-br and br_1971. |
| `ptbr_divergences.json` | The PT/BR divergence pairs and the nasal-vowel alternation (`connosco` and `conosco`). |
| `sister_markers.json` | The markers that the guard uses for Mirandese, Galician and Barranquenho. |
| `detector_nb.json` | The shipped Naive Bayes model of `detect(method="nb")`. |
| `detector_perceptron.json` | The shipped averaged perceptron of `detect(method="perceptron")`. |

`get_lexicon()` loads these files, except the two detector models, and exposes them as maps. `ml.get_detector_model()` loads the detector models. [The API reference](api.md#lexicon) lists the maps.

## Check a row

Each row of the spelling table names its norm and its source:

```python
>>> import json
>>> from importlib.resources import files
>>> rows = json.loads(files("desacordo_ortografico").joinpath("data/spelling.json").read_text(encoding="utf-8"))["rows"]
>>> sorted(rows[0])
['curated', 'era', 'form', 'source', 'target', 'value']
>>> sum(r["era"] == "reforma_1911" for r in rows)
15
```

## Hugging Face datasets

`benchmark/publish_hf.py --spelling` builds the datasets `TigreGotico/archaisms_pt`, `TigreGotico/AO1990_pt-PT` and `TigreGotico/AO1990_pt-BR` from the spelling table of the checkout. Each CSV keeps the line order of the file on the Hub and takes its spellings from the table. Each file drops the line of an old form that no older norm wrote. These are aréia, réida and zéida, the pt-BR co-directora, zoelectricidade and dielectricidade, and the pre-1911 phlegmon.

`--dry-run DIR` writes each CSV and its dataset card to `DIR/<dataset>/` and uploads nothing. `--upload --base DIR` uploads a reviewed dry run. A change to the table reaches the Hub only after an upload. The script needs `huggingface_hub`, which the package does not install.

Language models wrote a parallel silver corpus, and no person checked it. It is published as [TigreGotico/desacordo_ortografico](https://huggingface.co/datasets/TigreGotico/desacordo_ortografico). The [benchmark README](../benchmark/README.md) describes it.

---
[← Orthographies](orthographies.md) · [Home](index.md)
