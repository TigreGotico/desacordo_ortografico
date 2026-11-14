#!/usr/bin/env python3
"""Publish the parallel silver corpus as a Hugging Face dataset.

Flattens the nested cells into one column per norm (viewer-friendly), writes a dataset
card, and uploads to ``TigreGotico/desacordo_ortografico``.

    python benchmark/publish_hf.py [--repo TigreGotico/desacordo_ortografico] [--private]
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
NORMS = ["etymological", "pt_1973", "ao1990-pt", "br_1971", "ao1990-br"]


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

A last step corrects the Brazilian cells of all rows from dictionaries. The Vocabulário
Ortográfico da Língua Portuguesa (VOLP) of the Academia Brasileira de Letras decides
first, then the Brazilian headword of the Priberam dictionary, then Michaelis. Where the
VOLP lists both forms of a word, the cell writes the c/p form (`facto`, `sector`,
`detectar`). Where it lists one form, the cell writes that form (`ação`, `acepção`,
`comitê`). The `br_1971` cells write the preterite ending `-amos` without the accent. A
row with a word whose Brazilian spelling the sources do not decide is dropped.

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


def main():
    from huggingface_hub import HfApi

    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="TigreGotico/desacordo_ortografico")
    ap.add_argument("--private", action="store_true")
    args = ap.parse_args()

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

        api = HfApi()
        api.create_repo(args.repo, repo_type="dataset", private=args.private, exist_ok=True)
        api.upload_folder(folder_path=d, repo_id=args.repo, repo_type="dataset",
                          commit_message="Publish Portuguese orthographies parallel corpus")
    print(f"published {len(parallel)} parallel + {len(sisters)} sister rows to "
          f"https://huggingface.co/datasets/{args.repo}")


if __name__ == "__main__":
    main()
