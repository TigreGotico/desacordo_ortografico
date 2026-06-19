#!/usr/bin/env python3
"""Publish the scraped Acordo Ortográfico word-change lexicon to the Hugging Face Hub.

    python tools/publish_portuguesaletra_hf.py [--repo TigreGotico/acordo-ortografico-lexicon]
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

CARD = """---
license: other
language:
- pt
task_categories:
- text-classification
- translation
tags:
- portuguese
- orthography
- acordo-ortografico
- ao1990
- lexicon
- historical-linguistics
size_categories:
- 1K<n<10K
---

# Acordo Ortográfico de 1990 — Word-Change Lexicon

{N} Portuguese words documented across the 1990 orthographic reform: the pre-1990
European (1945) and Brazilian (1943) spellings, the AO1990 valid form(s), and whether the
spelling changed. **{C}** of them have a changed European or Brazilian spelling.

## Columns

| column | meaning |
|--------|---------|
| `title` | the word, as headed on the source page |
| `eu_1945` | pre-1990 European form(s) (list) |
| `br_1943` | pre-1990 Brazilian form(s) (list) |
| `ao1990` | AO1990 valid form(s) (list) |
| `notes` | the *observação* (usage restrictions, e.g. "X não é usado no Brasil") |
| `changed` | did the spelling change, per the source's note (`true` / `false` / `null`) |
| `eu_changed` | the pre-1990 European form is not among the AO1990 forms |
| `br_changed` | the pre-1990 Brazilian form is not among the AO1990 forms |
| `slug`, `url` | source-page identifiers |

## Change types covered

Every AO1990 mechanism appears: silent c/p (`protectorato → protetorato`), open-diphthong
accent (`mongolóide → mongoloide`), prefix hyphen collapsing to a doubled r/s
(`anti-sepsia → antissepsia`, `ultra-sonoro → ultrassonoro`), and lexicalised hyphenation
(`neo-romântica → neorromântica`).

## Source & attribution

Compiled by scraping the *Acordo Ortográfico* category of **Português à Letra**
([portuguesaletra.com](https://portuguesaletra.com/category/acordo-ortografico/)) with the
open-source client in
[`desacordo_ortografico/tools`](https://github.com/TigreGotico/desacordo_ortografico).
The orthographic entries are the work of Português à Letra — please credit the source and
respect their terms; the spelling norms themselves are factual. Apache-2.0 covers only the
scraping/packaging code, not the underlying content.
"""


def main():
    from huggingface_hub import HfApi

    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="TigreGotico/acordo-ortografico-lexicon")
    ap.add_argument("--data", default=os.path.join(HERE, "portuguesaletra_ao.jsonl"))
    ap.add_argument("--private", action="store_true")
    args = ap.parse_args()

    rows = [json.loads(line) for line in open(args.data, encoding="utf-8") if line.strip()]
    changed = sum(1 for r in rows if r["changed"] or r["eu_changed"] or r["br_changed"])

    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "words.jsonl"), "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(os.path.join(d, "README.md"), "w", encoding="utf-8") as f:
            f.write(CARD.replace("{N}", str(len(rows))).replace("{C}", str(changed)))

        api = HfApi()
        api.create_repo(args.repo, repo_type="dataset", private=args.private, exist_ok=True)
        api.upload_folder(folder_path=d, repo_id=args.repo, repo_type="dataset",
                          commit_message="Publish AO1990 word-change lexicon (portuguesaletra.com)")
    print(f"published {len(rows)} words ({changed} changed) to "
          f"https://huggingface.co/datasets/{args.repo}")


if __name__ == "__main__":
    main()
