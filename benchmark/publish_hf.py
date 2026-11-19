#!/usr/bin/env python3
"""Publish the desacordo_ortografico datasets on the Hugging Face Hub.

The parallel silver corpus goes to ``TigreGotico/desacordo_ortografico``. The script
flattens the nested cells into one column per norm (viewer-friendly), writes a dataset
card, and uploads the corpus with its card:

    python benchmark/publish_hf.py [--repo TigreGotico/desacordo_ortografico] [--private]

``--spelling`` builds the three spelling datasets from the spelling table
``desacordo_ortografico/data/spelling.json`` of this checkout: ``TigreGotico/archaisms_pt``,
``TigreGotico/AO1990_pt-PT`` and ``TigreGotico/AO1990_pt-BR``. Each file keeps the lines,
the line order and the notes of the file on the Hub, and takes its spelling data from the
table. The script reads the Hub files at the main revision of each repo, or the files of
an earlier dry run with ``--base DIR``. ``--dry-run DIR`` writes the CSV and the dataset
card of each one to ``DIR/<dataset>/``, and the Hub revision that each file comes from to
``DIR/revisions.json``. It uploads nothing. ``--upload --base DIR`` uploads the CSV and the
card of each folder of the dry run in DIR as they are. It stops before the first upload when
the head of any of the three repos is no longer the revision that the dry run read, and each
upload names that revision as the parent commit:

    python benchmark/publish_hf.py --spelling --dry-run out/
    python benchmark/publish_hf.py --spelling --base out/ --dry-run out2/
    python benchmark/publish_hf.py --spelling --upload --base out2/
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import tempfile
from collections import defaultdict

import desacordo_ortografico
from desacordo_ortografico import convert
from desacordo_ortografico.lexicon import Lexicon, deaccent

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACKAGE = os.path.join(ROOT, "desacordo_ortografico")
TABLE = os.path.join(PACKAGE, "data", "spelling.json")
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

#: Pre-1911 rows of the table that archaisms_pt leaves out. kermesse is the French spelling,
#: "the same class as homme", and not a pre-1911 Portuguese form
#: (knowledge/wiki/plans/desacordo-architecture-fixes.md). Its row stays in the table,
#: because 1911 Base I respells the French word: "Escreveremos, pois, caleidoscópio, quermes".
FOREIGN_SPELLINGS = frozenset({"kermesse"})

#: pt-BR rows of the table that AO1990_pt-BR leaves out until a source decides them. The VOLP
#: has no entry for reta-pronúncia or recta-pronúncia, and recta is no spelling of the
#: Formulário Ortográfico of 1943.
UNSOURCED_PT_BR = frozenset({"recta-pronúncia"})

#: Old forms of the Hub files that no older norm wrote, by era. The table has no row for
#: them, and the dry run drops their lines. The 1943 ABL vocabulary lists areia and reida
#: with no accent, and the VOLP and the VOP mark the ei of areia, reida and zeida neither open
#: nor accented. No source gives aréia, réida or zéida. phlegmon is the French and English
#: spelling: Figueiredo (1913) has "Phlegmão, m. (V. fleimão)" and no phlegmon.
WITHDRAWN = {"etymological": frozenset({"phlegmon"}),
             "pt_1973": frozenset({"réida", "zéida"}),
             "br_1971": frozenset({"aréia", "réida", "zéida"})}

#: The letter changes of a pre-1911 form, in the notation of the tugalex archaisms list. Each
#: rule rewrites the archaic form, without accents, when the modern form has the pattern
#: fewer times, gains the letters that the rule writes, and is nearer to the rewritten form.
#: A rule that fires gives its note, and the later rules read the rewritten form: diphthongo
#: gives "phth→t", and no "ph→f". phlegma -> fleuma gives no "gm→m", because the modern form
#: has gm -> um.
_LETTER_CHANGES = [
    # pattern, replacement, note, letters that the modern form gains
    ("symph", "sinf", "symph→sinf", "n"),
    ("phth", "t", "phth→t", ""),
    ("ph", "f", "ph→f", "f"),
    ("th", "t", "th→t", ""),
    ("rh", "r", "rh→r", ""),
    ("ch(?=[eiy])", "qu", "ch→qu", "qu"),
    ("ch", "c", "ch→c", ""),
    ("y", "i", "y→i", "i"),
    ("k(?=[ei])", "qu", "k→qu", "qu"),
    ("k", "c", "k→c", "c"),
    ("w", "v", "w→v", "v"),
    ("w", "u", "w→u", "u"),
    *[(x + x, x, f"{x}{x}→{x}", "") for x in "bcdfglmnpt"],
    ("mn", "n", "mn→n", ""),
    ("gn", "n", "gn→n", ""),
    ("gm", "m", "gm→m", ""),
    ("mp(?=t)", "n", "mp→n", "n"),
    ("m(?=[cdfgjlnqrstvz])", "n", "m→n", "n"),
    ("[cp](?=[tç])|^s(?=c[ei])", "", "silent consonant", ""),
    ("^p(?=s)", "", "ps→s", ""),
    ("h", "", "h dropped", ""),
]


def _count(pattern: str, word: str) -> int:
    return len(re.findall(pattern, word))


def _distance(a: str, b: str) -> int:
    """The Levenshtein distance between ``a`` and ``b``."""
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        diagonal, row[0] = row[0], i
        for j, y in enumerate(b, 1):
            diagonal, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, diagonal + (x != y))
    return row[-1]


def letter_changes(archaic: str, modern: str) -> str:
    """The letter changes from ``archaic`` to ``modern``, such as "ph→f + y→i"."""
    a, m = deaccent(archaic), deaccent(modern)
    found = []
    for pattern, replacement, note, gain in _LETTER_CHANGES:
        if _count(pattern, a) > _count(pattern, m) and (not gain or _count(gain, m) > _count(gain, a)):
            rewritten = re.sub(pattern, replacement, a)
            if _distance(rewritten, m) < _distance(a, m):
                a = rewritten
                found.append(note)
    return " + ".join(dict.fromkeys(found))


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


#: A full Hub commit sha.
_SHA = re.compile(r"[0-9a-f]{40}")


def _revisions(base: str) -> dict[str, str]:
    """The Hub revision of each dataset file of the dry run in ``base``."""
    path = os.path.join(base, "revisions.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def base_lines(repo: str, filename: str, base: str | None = None) -> tuple[list[list[str]], str | None]:
    """The lines of the file of a dataset, the header first, and the Hub revision of the
    file: the file at the main revision on the Hub, or the file in ``base/<dataset>/``."""
    if base:
        path = os.path.join(base, repo.split("/")[1], filename)
        revision = _revisions(base).get(repo)
    else:
        from huggingface_hub import HfApi, hf_hub_download

        revision = HfApi().dataset_info(repo).sha
        path = hf_hub_download(repo, filename, repo_type="dataset", revision=revision)
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.reader(f)), revision


def _forms(field: str) -> list[str]:
    return [w.strip() for w in field.split(",")]


def _after_anchors(base: list[str], table: list[str], skip=frozenset()) -> list[str]:
    """``base`` with each word of ``table`` that it lacks, after the word that comes before
    it in ``table``."""
    after: dict[str | None, list[str]] = defaultdict(list)
    anchor = None
    listed = set(base)
    for word in table:
        if word in skip:
            continue
        if word in listed:
            anchor = word
        else:
            after[anchor].append(word)
    out = list(after[None])
    for word in base:
        out.append(word)
        out.extend(after[word])
    return out


def archaism_rows(table: list[dict], lex: Lexicon, lines: list[list[str]]) -> list[dict]:
    """One row for each pre-1911 form of the spelling table, in the order of ``lines``, the
    file on the Hub. A form that the file lacks comes after the form before it in the table.

    A form with an AO1990 row of its own takes the AO1990 forms of the table, and the VOLP
    decides its pt-BR form, as convert() does for a pt-BR word. convert() does not read
    those rows, so every other form takes the forms that convert() gives it. ``notes`` is
    the note of the file, which is the note of the tugalex archaisms list, else the note of
    the table row, else the letter changes of the pair.
    """
    cells: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in table:
        if r["era"] == "etymological":
            cells[r["form"]][r["target"]] = r
    listed = {line[0]: line[3] for line in lines[1:] if line[0] not in WITHDRAWN["etymological"]}
    missing = set(listed) - set(cells)
    if missing:
        raise ValueError(f"the spelling table lacks the pre-1911 forms {sorted(missing)}")
    out = []
    for form in _after_anchors(list(listed), list(cells), FOREIGN_SPELLINGS):
        cell = cells[form]
        if "ao1990-pt" in cell:
            modern = cell["ao1990-pt"]["value"]
            br = cell["ao1990-br"]["value"] if "ao1990-br" in cell else modern
            br = lex.ao_br_volp.get(br, br)
        else:
            modern = convert(form, "etymological", "ao1990-pt")
            br = convert(form, "etymological", "ao1990-br")
        source = next(iter(cell.values()))["source"]
        noted = _ARCHAISM_NOTES.fullmatch(source)
        notes = listed.get(form) or (noted.group(1) if noted else letter_changes(form, modern) or source)
        out.append({"archaic": form, "modern": modern, "modern_pt_BR": "" if br == modern else br,
                    "notes": notes})
    return out


def ao_rows(table: list[dict], era: str, lines: list[list[str]],
            volp: dict[str, str] | None = None) -> list[dict]:
    """The AO1990 rows of one variety, on ``lines``, the lines of the file on the Hub.

    The file can give one old form on two lines, and its reader keeps the later line. The
    later line takes the AO1990 forms of the table, and an earlier one stays as written. A
    line keeps its text where the table gives the forms that it has. A line that adds no
    form to the lines before it goes, and so does a line equal to an earlier one. An old
    form that the file lacks comes on a line of its own, after the old form before it in
    the table. A dual cell joins its forms with ", ", in source order.

    ``volp`` maps an AO1990 word to its form in the VOLP. A cell with one form takes its VOLP
    form, as convert() does: "VOLP: intersectar v.; no intersetar".
    """
    def forms(value: str) -> list[str]:
        cell = value.split("|")
        if volp and len(cell) == 1:
            cell = [volp.get(cell[0], cell[0])]
        return cell

    cells = {r["form"]: forms(r["value"]) for r in table
             if r["era"] == era and not (era == "br_1971" and r["form"] in UNSOURCED_PT_BR)}
    withdrawn = WITHDRAWN.get(era, frozenset())
    lines = [line for line in lines[1:] if not set(_forms(line[0])) <= withdrawn]
    last = {old: i for i, (olds, _new) in enumerate(lines) for old in _forms(olds)}
    missing = set(last) - set(cells)
    if missing:
        raise ValueError(f"the spelling table lacks the {era} forms {sorted(missing)}")
    out: list[dict] = []
    written: dict[str, str] = {}
    line_of: dict[str, int] = {}
    for i, (olds, new) in enumerate(lines):
        groups: dict[str, list[str]] = {}
        for old in _forms(olds):
            value = cells[old] if last[old] == i else _forms(new)
            groups.setdefault(", ".join(value), []).append(old)
        for value, group in groups.items():
            if all(written.get(old) == value for old in group):
                continue
            whole = group == _forms(olds)
            out.append({"old_form": olds if whole else ", ".join(group),
                        "new_form": new if value == ", ".join(_forms(new)) else value})
            for old in group:
                written[old] = value
                line_of[old] = len(out) - 1
    after: dict[int, list[dict]] = defaultdict(list)
    anchor = -1
    for old, value in cells.items():
        if old in last:
            anchor = line_of[old]
        else:
            after[anchor].append({"old_form": old, "new_form": ", ".join(value)})
    return after[-1] + [row for j, line in enumerate(out) for row in [line, *after[j]]]


def write_spelling(out_dir: str, base: str | None = None) -> dict[str, str]:
    """Write the CSV and the dataset card of each spelling dataset to ``out_dir/<dataset>/``,
    on the lines of the Hub file or of the file in ``base/<dataset>/``, and the Hub revision
    of each file to ``out_dir/revisions.json``. Return the folder of each dataset repo."""
    imported = os.path.dirname(os.path.realpath(desacordo_ortografico.__file__))
    if imported != os.path.realpath(PACKAGE):
        sys.exit(f"publish_hf.py: desacordo_ortografico is imported from {imported}, not from "
                 f"this checkout ({PACKAGE}). Install the checkout or put it on PYTHONPATH.")
    with open(TABLE, encoding="utf-8") as f:
        data = json.load(f)
    table = data["rows"]
    folders = {}
    revisions = {}
    for repo, (era, filename, columns, newline) in SPELLING_DATASETS.items():
        lex = Lexicon()
        lines, revision = base_lines(repo, filename, base)
        if revision:
            revisions[repo] = revision
        if era == "etymological":
            rows = archaism_rows(table, lex, lines)
        else:
            rows = ao_rows(table, era, lines, lex.ao_br_volp if era == "br_1971" else None)
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
    with open(os.path.join(out_dir, "revisions.json"), "w", encoding="utf-8") as f:
        json.dump(revisions, f, indent=2)
        f.write("\n")
    return folders


def upload_spelling(api, base: str) -> None:
    """Upload the CSV and the card of each spelling dataset in ``base``, a reviewed dry run,
    as they are. The upload stops before it sends a file when a file is missing, when a
    revision of ``revisions.json`` is not a commit sha, or when the head of a repo is no
    longer that revision. The parent commit of each upload is that revision, so a commit
    between the check and the upload makes the upload fail."""
    revisions = _revisions(base)
    for repo, (_era, filename, _columns, _newline) in SPELLING_DATASETS.items():
        folder = os.path.join(base, repo.split("/")[1])
        revision = revisions.get(repo)
        if not isinstance(revision, str) or not _SHA.fullmatch(revision):
            sys.exit(f"publish_hf.py: {base}/revisions.json gives no commit sha for {repo}: {revision!r}")
        for name in (filename, "README.md"):
            if not os.path.isfile(os.path.join(folder, name)):
                sys.exit(f"publish_hf.py: {folder} has no {name}")
    for repo in SPELLING_DATASETS:
        head = api.dataset_info(repo).sha
        if head != revisions[repo]:
            sys.exit(f"publish_hf.py: the head of {repo} is {head}, not {revisions[repo]}, the "
                     "revision of the dry run. Make a new dry run and review it.")
    for repo, (_era, filename, _columns, _newline) in SPELLING_DATASETS.items():
        api.upload_folder(folder_path=os.path.join(base, repo.split("/")[1]), repo_id=repo,
                          repo_type="dataset", parent_commit=revisions[repo],
                          allow_patterns=[filename, "README.md"],
                          commit_message="Publish from the desacordo_ortografico spelling table")
        print(f"published https://huggingface.co/datasets/{repo}")


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
    ap.add_argument("--base", metavar="DIR",
                    help="with --spelling: read the file of each dataset from DIR/<dataset>/, "
                         "not from the Hub")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", metavar="DIR",
                      help="with --spelling: write each dataset to DIR/<dataset>/ and upload nothing")
    mode.add_argument("--upload", action="store_true",
                      help="with --spelling and --base DIR: upload the dry run in DIR")
    args = ap.parse_args()

    if args.spelling:
        if args.dry_run:
            write_spelling(args.dry_run, args.base)
            return
        if not args.upload:
            ap.error("--spelling needs --dry-run DIR or --upload --base DIR")
        if not args.base:
            ap.error("--upload needs --base DIR, the folder of a reviewed dry run")
        from huggingface_hub import HfApi

        upload_spelling(HfApi(), args.base)
        return
    if args.dry_run or args.upload or args.base:
        ap.error("--dry-run, --upload and --base go with --spelling")

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
