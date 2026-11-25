# Tools

<!-- agent-hint
covers: the scripts under tools/: the spelling-table builder, the documentation chart builder and the portuguesaletra scraper and publisher
source: `tools/build_spelling_table.py`, `tools/build_docs_plots.py`, `tools/scrape_portuguesaletra.py`, `tools/publish_portuguesaletra_hf.py`
generated: no
verify: for f in tools/*.py; do python -m py_compile "$f" || exit 1; done
see: `../docs/index.md`, `../docs/data.md`, `../AGENTS.md`
-->

This folder holds the scripts that build the data and the charts of the repository. Four scripts live here. Each section below shows the command and what it makes.

## `scrape_portuguesaletra.py`

A small, stdlib-only client that scrapes the *Acordo Ortográfico* category of [portuguesaletra.com](https://portuguesaletra.com/category/acordo-ortografico/) into a dataset of words whose spelling the 1990 reform touched.

Each article documents one vocábulo with a fixed, labelled layout. The layout holds the pre-1990 European form (`Ortografia Antiga _1945`), the pre-1990 Brazilian form (`Ortografia Antiga _1943`), the AO1990 valid forms (`vocábulo(s) válido(s)`) and an `observações` note. The client parses each article into one JSON record.

```bash
python tools/scrape_portuguesaletra.py -o tools/portuguesaletra_ao.jsonl --delay 0.4
```

It walks the 263 category pages, then streams ~6.5k records to disk (flushed per row). Polite by default: a real User-Agent, a delay between requests, retries with back-off, and it honours the site's robots.txt (which only blocks `/cgi-bin` and named bad bots).

### Record schema

```json
{
  "slug": "protectorato-ou-protetorato-ao",
  "url":  "https://portuguesaletra.com/acordo-ortografico/protectorato-ou-protetorato-ao/",
  "title": "Protectorato ou Protetorato",
  "eu_1945": ["protectorato"],          // pre-1990 European form(s)
  "br_1943": ["protetorato"],           // pre-1990 Brazilian form(s)
  "ao1990":  ["protetorato"],           // AO1990 valid form(s)
  "notes":   "situação anterior é alterada!",
  "changed":    true,                   // from the observação note (true|false|null)
  "eu_changed": true,                   // European pre-1990 form not among the AO1990 forms
  "br_changed": false                   // Brazilian pre-1990 form not among the AO1990 forms
}
```

### Dataset

One run gave 6,568 words. Of these, **2,897** have a changed European or Brazilian spelling. The changes cover every AO1990 mechanism: silent c/p (`protectorato→protetorato`), open diphthong (`mongolóide→mongoloide`), prefix hyphen → doubled r/s (`anti-sepsia→antissepsia`, `ultra-sonoro→ultrassonoro`), and lexicalised hyphenation (`neo-romântica→neorromântica`).

The output `.jsonl` is git-ignored and the script can regenerate it. The content comes from portuguesaletra.com, so check the terms of the site before you redistribute it.

## `build_spelling_table.py`

Builds `desacordo_ortografico/data/spelling.json`, the spelling table that `convert()` and `detect()` read. It reads the curated 1911 pairs, their sources and the comment of each group, and the tugalex archaisms and AO1990 lists. It sorts each archaism row by the reform that its modern form rests on. A row whose 1911 form is known becomes a pre-1911 -> 1911 row. Every other archaism row gives only its AO1990 forms.

```bash
python tools/build_spelling_table.py --curated-json reform_1911_irregular.json
```

The table came from one run with the tugalex release that the package pins as its floor. `--curated-json` takes `data/reform_1911_irregular.json` of a desacordo_ortografico release that ships it, such as 0.2.1a1. The script writes the two sources that this file has without accents as the works print them (`CITATIONS` in the script). The data file is edited by hand from then on. Without `--curated-json`, the script keeps the curated rows, `_sources` and `_groups` of the table and rebuilds the other rows. Both runs give the committed file byte for byte.

## `publish_portuguesaletra_hf.py`

Uploads the scraped words to the Hugging Face dataset `TigreGotico/acordo-ortografico-lexicon`, with a dataset card that credits the source site. It needs `huggingface_hub`, which the package does not install, and the `.jsonl` file that the scraper writes.

```bash
python tools/publish_portuguesaletra_hf.py --data tools/portuguesaletra_ao.jsonl
```

`--repo` names another dataset, and `--private` makes the dataset private. The script prints the number of words and the number of changed words when the upload ends.

## `build_docs_plots.py`

Draws the chart of [the features page](../docs/features.md): how many distinct words of the silver corpus each conversion feature changes. It uses only the standard library to draw, and it writes a light and a dark SVG to `docs/assets/`.

```bash
python tools/build_docs_plots.py --count   # recount with the package, write docs/assets/feature_words.json
python tools/build_docs_plots.py --write   # draw the two SVG files from the counts
python tools/build_docs_plots.py --check   # exit 1 when an SVG differs from its drawing
```

`--count` converts every distinct word of three routes with all features on, and again once per feature with that feature off. It needs the package installed. The test `tests/test_docs_plots.py` runs the check of `--check`.

---
[Documentation index](../docs/index.md)
