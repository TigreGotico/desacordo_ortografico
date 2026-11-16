#!/usr/bin/env python3
"""Publish the desacordo_ortografico datasets on the Hugging Face Hub.

The parallel silver corpus goes to ``TigreGotico/desacordo_ortografico``. The script
flattens the nested cells into one column per norm (viewer-friendly), writes a dataset
card, and uploads the corpus with its card:

    python benchmark/publish_hf.py [--repo TigreGotico/desacordo_ortografico] [--private]

``--spelling`` builds the three spelling datasets from the spelling table
``desacordo_ortografico/data/spelling.json``: ``TigreGotico/archaisms_pt``,
``TigreGotico/AO1990_pt-PT`` and ``TigreGotico/AO1990_pt-BR``. ``--dry-run DIR`` writes
the CSV and the dataset card of each one to ``DIR/<dataset>/`` and uploads nothing.
Only ``--upload`` uploads them:

    python benchmark/publish_hf.py --spelling --dry-run out/
    python benchmark/publish_hf.py --spelling --upload
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import tempfile
from collections import defaultdict
from importlib.resources import files

from desacordo_ortografico import convert
from desacordo_ortografico.lexicon import Lexicon

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS = os.path.join(HERE, "hf_cards")
NORMS = ["etymological", "pt_1973", "ao1990-pt", "br_1971", "ao1990-br"]

#: Each spelling dataset: the era of its table rows, and its file, columns and line ending
#: as the Hub files have them.
SPELLING_DATASETS = {
    "TigreGotico/archaisms_pt": ("etymological", "archaisms.csv",
                                 ["archaic", "modern", "modern_pt_BR", "notes"], "\n"),
    "TigreGotico/AO1990_pt-PT": ("pt_1973", "acordo_ortografico_pt_PT.csv",
                                 ["old_form", "new_form"], "\r\n"),
    "TigreGotico/AO1990_pt-BR": ("br_1971", "acordo_ortografico_pt_BR.csv",
                                 ["old_form", "new_form"], "\r\n"),
}

#: The source of a row that the tugalex archaisms list gave, with the letter changes of the row.
_ARCHAISM_NOTES = re.compile(r"tugalex archaisms\.csv \((.*)\)")


def _load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def flatten_parallel(rows):
    out = []
    for r in rows:
        flat = {"id": r["id"], "source": r.get("source", "authored"),
                "features": r.get("features", [])}
        for n in NORMS:
            flat[n.replace("-", "_")] = r["cells"][n]
        out.append(flat)
    return out


CARD = """---
license: apache-2.0
language:
- pt
multilinguality:
- monolingual
task_categories:
- text-classification
- translation
tags:
- portuguese
- orthography
- acordo-ortografico
- ao1990
- parallel-corpus
- historical-linguistics
size_categories:
- 10K<n<100K
configs:
- config_name: parallel
  data_files: parallel.jsonl
  default: true
- config_name: sisters
  data_files: sisters.jsonl
---

# Portuguese Orthographies — Parallel Corpus

A parallel corpus for **detecting and converting between Portuguese orthographies**. Each
record is one Portuguese sentence written in five orthographic norms, so the same content
can be aligned across the spelling reforms of the language.

## Norms (one column each)

| column | norm |
|--------|------|
| `etymological` | pre-1911 pseudo-etymological spelling |
| `pt_1973` | pre-AO1990 European (Convenção 1945 + 1973 mini-reform) |
| `ao1990_pt` | Acordo Ortográfico de 1990, European variant |
| `br_1971` | pre-AO1990 Brazilian (Formulário 1943 + 1971 mini-reform) |
| `ao1990_br` | Acordo Ortográfico de 1990, Brazilian variant |

The European line (`etymological`, `pt_1973`, `ao1990_pt`) and the Brazilian line
(`br_1971`, `ao1990_br`) may differ in lexis as well as spelling (e.g. *ficheiro* /
*arquivo*); within each line the cells differ only by the documented era transforms.

## Configs

- **parallel** (default) — {N} sentences × 5 norms, each with a `features` list naming the
  orthographic phenomena it exercises (digraphs, silent consonants, nasal vowels, trema,
  differential accents, hyphenation, …) and a `source` field (see Construction).
- **sisters** — short samples of Mirandese, Galician and Barranquenho (recognised
  varieties that are not Portuguese orthographies) plus Portuguese controls, for a
  language-guard task.

## Construction

All rows are silver data. Language models wrote the sentences or classified the words
they are built from, and no person checked them.

The `source` field marks how each row was built:

- `authored` — language models wrote the sentence in all five norms against a per-norm
  rule card. A language-model QA pass then corrected or dropped rows. A consistency step
  replaced some dual and divergence words with the variants of the converter's word maps,
  and some etymological words with their `pt_1973` forms.
- `derived` — a modern European sentence that a language model wrote. Per-word table
  lookup and deterministic rules (nasal vowel, trema, month casing) produce the other
  four norms. The tables come from the `authored` rows, the AO1990 and 1911 word maps of
  the converter's lexicon, and a word list that a language-model panel classified one by
  one. A sentence that holds a word no table covers is dropped. An error in a table goes
  into every row that uses the word.
- `coverage` — a short carrier sentence (one quoted term), derived the same way, so that
  **every** AO1990-changed word in the reference lexicon appears at least once.

A last step corrects the Brazilian cells of all rows from dictionaries. The `br_1971`
cells follow the Formulário Ortográfico of 1943 of the Academia Brasileira de Letras,
then the Pequeno Vocabulário Ortográfico of 1943 that the Formulário opens, then the
Brazilian headword of the Priberam dictionary before the AO1990, where the page shows a
spelling change. Where rule 18 of the Formulário or an entry of the vocabulary registers
both forms, the cell writes the c/p form (`contacto`, `secção`, `tecto`, `sector`,
`corrupto`); rule 16 keeps `ótimo`, and the vocabulary writes `conjetura` and `clichê`. The `ao1990_br` cells follow the Vocabulário
Ortográfico da Língua Portuguesa (VOLP), then Priberam after the AO1990, where the page
shows a spelling change.
Where the VOLP lists both forms of one word, the cell writes the c/p form (`facto`,
`sector`, `detectar`). Where it lists one form, the cell writes that form (`ação`,
`acepção`, `comitê`). The `br_1971` cells write the preterite ending `-amos` without the
accent. A word that no source of its cell decides stays as written in its row, and so
does a personal or place name inside a sentence (`Otávia`, `o Ártico`). Two rows
are dropped: the VOLP lists no form of their word (`detetiva`), or the sentence fits
neither of two VOLP words (`distático`).

Within each line (European: `etymological`/`pt_1973`/`ao1990_pt`; Brazilian:
`br_1971`/`ao1990_br`) the cells differ only by the documented era transforms; the two
national lines may also differ lexically in the `authored` rows.

## Word coverage

**Every** AO1990-changed word in the reference lexicon appears at least once — silent c/p
(`acção`, `óptimo`, `director`), trema (`freqüência`, `lingüiça`), open-diphthong accent
(`idéia`, `heróico`), and dual/divergence (`facto`/`fato`, `húmido`/`úmido`) are each at
100% of their inventory.

## Uses

- Benchmark or train a Portuguese orthography **detector** (classify which norm a text is in).
- Benchmark an orthography **converter** (transform between norms) — note that the two
  national lines can diverge lexically, which an orthographic converter does not translate.

## Source

Produced for the [`desacordo_ortografico`](https://github.com/TigreGotico/desacordo_ortografico)
library. Apache-2.0.
"""


def archaism_rows(table: list[dict], lex: Lexicon) -> list[dict]:
    """One row for each pre-1911 form of the spelling table, in table order.

    A form with an AO1990 row of its own takes the AO1990 forms of the table, and the VOLP
    decides its pt-BR form, as convert() does for a pt-BR word. convert() does not read
    those rows, so every other form takes the forms that convert() gives it.
    """
    cells: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in table:
        if r["era"] == "etymological":
            cells[r["form"]][r["target"]] = r
    out = []
    for form, cell in cells.items():
        if "ao1990-pt" in cell:
            modern = cell["ao1990-pt"]["value"]
            br = cell["ao1990-br"]["value"] if "ao1990-br" in cell else modern
            br = lex.ao_br_volp.get(br, br)
        else:
            modern = convert(form, "etymological", "ao1990-pt")
            br = convert(form, "etymological", "ao1990-br")
        notes = _ARCHAISM_NOTES.fullmatch(next(iter(cell.values()))["source"])
        out.append({"archaic": form, "modern": modern, "modern_pt_BR": "" if br == modern else br,
                    "notes": notes.group(1) if notes else ""})
    return out


def ao_rows(table: list[dict], era: str) -> list[dict]:
    """The AO1990 rows of one variety. A dual cell joins its forms with ", ", in source order."""
    return [{"old_form": r["form"], "new_form": ", ".join(r["value"].split("|"))}
            for r in table if r["era"] == era]


def write_spelling(out_dir: str) -> dict[str, str]:
    """Write the CSV and the dataset card of each spelling dataset to ``out_dir/<dataset>/``.
    Return the folder of each dataset repo."""
    data = json.loads((files("desacordo_ortografico") / "data" / "spelling.json").read_text("utf-8"))
    table = data["rows"]
    folders = {}
    for repo, (era, filename, columns, newline) in SPELLING_DATASETS.items():
        rows = archaism_rows(table, Lexicon()) if era == "etymological" else ao_rows(table, era)
        name = repo.split("/")[1]
        folder = os.path.join(out_dir, name)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, filename), "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, columns, lineterminator=newline)
            writer.writeheader()
            writer.writerows(rows)
        cited = [s for s in data["_sources"]
                 if any(r["era"] == era and r["source"].startswith(s) for r in table)]
        with open(os.path.join(CARDS, f"{name}.md"), encoding="utf-8") as f:
            card = f.read()
        with open(os.path.join(folder, "README.md"), "w", encoding="utf-8") as f:
            f.write(card.replace("{rows}", f"{len(rows):,}")
                    .replace("{sources}", "\n".join(f"- {s}" for s in cited)))
        folders[repo] = folder
        print(f"{repo}: {len(rows)} rows -> {folder}")
    return folders


def _upload(api, repo: str, folder: str, private: bool, message: str) -> None:
    # create_repo counts against the account's daily repo-creation limit, even for a repo
    # that exists, so it runs only for a missing repo
    if not api.repo_exists(repo, repo_type="dataset"):
        api.create_repo(repo, repo_type="dataset", private=private, exist_ok=True)
    api.upload_folder(folder_path=folder, repo_id=repo, repo_type="dataset",
                      commit_message=message)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="TigreGotico/desacordo_ortografico")
    ap.add_argument("--private", action="store_true")
    ap.add_argument("--spelling", action="store_true",
                    help="build the archaisms_pt, AO1990_pt-PT and AO1990_pt-BR datasets "
                         "from the spelling table")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", metavar="DIR",
                      help="with --spelling: write each dataset to DIR/<dataset>/ and upload nothing")
    mode.add_argument("--upload", action="store_true", help="with --spelling: upload the datasets")
    args = ap.parse_args()

    if args.spelling:
        if args.dry_run:
            write_spelling(args.dry_run)
            return
        if not args.upload:
            ap.error("--spelling needs --dry-run DIR or --upload")
        from huggingface_hub import HfApi

        api = HfApi()
        with tempfile.TemporaryDirectory() as d:
            for repo, folder in write_spelling(d).items():
                _upload(api, repo, folder, args.private,
                        "Publish from the desacordo_ortografico spelling table")
                print(f"published https://huggingface.co/datasets/{repo}")
        return
    if args.dry_run or args.upload:
        ap.error("--dry-run and --upload go with --spelling")

    from huggingface_hub import HfApi

    parallel = flatten_parallel(_load("silver_full.jsonl"))
    sisters = _load("silver_sisters.jsonl")

    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "parallel.jsonl"), "w", encoding="utf-8") as f:
            for r in parallel:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(os.path.join(d, "sisters.jsonl"), "w", encoding="utf-8") as f:
            for r in sisters:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(os.path.join(d, "README.md"), "w", encoding="utf-8") as f:
            f.write(CARD.replace("{N}", str(len(parallel))))

        _upload(HfApi(), args.repo, d, args.private,
                "Publish Portuguese orthographies parallel corpus")
    print(f"published {len(parallel)} parallel + {len(sisters)} sister rows to "
          f"https://huggingface.co/datasets/{args.repo}")


if __name__ == "__main__":
    main()
