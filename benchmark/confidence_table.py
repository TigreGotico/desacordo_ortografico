"""Build the confidence table of ``detect(method="rules")``.

``detect()`` gives a label a fixed confidence: the held-out precision of that label for
its number of distinct evidence tokens (one, or two or more), from the population where
that precision is lowest. This script measures those precisions on the "cal" split and
prints the table that ``desacordo_ortografico/detect.py`` holds as ``_CONFIDENCE``. It
also prints the expected calibration error of the confidence that the installed
``detect()`` returns, on the "test" split.

Populations, each unit with a gold set of labels:

- book13: 13 pre-1911 Gutenberg books, each paragraph and each sentence, gold
  etymological. A book sentence with no old form is spelled the same in other norms, so
  book units count only when the label is etymological.
- pg31347: Eça de Queirós, Contos, Chardron 1913, printed in the 1911 spelling, gold
  reforma_1911. Most of its sentences hold no 1911 form and are spelled the same in later
  norms, so a pg31347 unit counts only when the label is reforma_1911. A book13 unit
  counts when the label is etymological or reforma_1911.
- silver_corpus: every rendering of the tracked ``benchmark/silver_corpus.jsonl``.
- silver_full: every rendering of ``parallel.jsonl`` of the Hugging Face dataset
  TigreGotico/desacordo_ortografico, in its own flat schema (one column per norm). The
  committed table comes from revision 7049ddd of that file (sha256 61f1a10a...5f5026):
  https://huggingface.co/datasets/TigreGotico/desacordo_ortografico/resolve/7049ddd/parallel.jsonl
- In both silver sets the gold set of a rendering is every norm whose column holds the
  same string.
- relabel: modern sentences of the "meio milhão de frases" corpus, gold etymological for
  the rows that ``--pre1911`` lists, else pt_1973, br_1971 or ao1990.

A unit's group (book id or row id) goes to "cal" when the sha1 of the group is even,
else to "test". pg31347 is always "test".

The evidence tokens of a label are the distinct words behind its markers (etym and
etym-pattern for etymological; verbal-eem, capital-month and pre-ao90-pt for pt_1973;
pre-ao90-br and trema for br_1971; reforma-1911 for reforma_1911), and for ao1990 the
distinct words of the AO1990 maps. A text with no marker and no AO1990 word keeps 0.34 and is no table cell. A cell
takes the lowest precision over the sources that hold at least ``MIN_UNITS`` cal units
in it, rounded to two decimals and capped at 0.99.

pg31347 is the only dated text in the 1911 spelling, and it is always "test", so no cal
unit has a true reforma_1911 label. A reforma_1911 cell that no source fills with
``MIN_UNITS`` cal units is provisional: it copies the etymological cell of the same
evidence count. The script prints every reforma_1911 unit by source, split and evidence
count, so the measured precision stands beside the provisional value.

The books are fetched from gutenberg.org into ``--books`` when they are missing. The
script prints the sha256 of every input file.

Usage:
    python benchmark/confidence_table.py --books DIR --silver-full parallel.jsonl \\
        --relabel rows.jsonl --pre1911 ids.txt [--labels out.tsv] [--check]

``--labels`` writes the label of every unit, for a label diff between two trees.
``--check`` exits non-zero when the table differs from ``_CONFIDENCE`` or when a
confidence that ``detect()`` returns differs from its table cell.
"""
import argparse
import collections
import hashlib
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

from desacordo_ortografico.detect import Orthography, detect
from desacordo_ortografico.lexicon import get_lexicon
from desacordo_ortografico.rules import _WORD_RE

Cell = Tuple[str, int]

BENCH = Path(__file__).resolve().parent
BOOKS = ["pg18220", "pg21406", "pg22044", "pg23145", "pg23203", "pg23400", "pg24401",
         "pg26850", "pg31347", "pg31971", "pg40409", "pg42942", "pg54829", "pg55752"]
SENT = re.compile(r"(?<=[.!?…])\s+(?=[\"“«—\-]?[A-ZÀ-Ý])")
FAMILY = {"etymological": "etymological", "pt_1973": "pt_1973", "br_1971": "br_1971",
          "ao1990-pt": "ao1990", "ao1990-br": "ao1990"}
# the columns of the Hugging Face parallel.jsonl, as the norm ids of silver_corpus.jsonl
HF_COLUMNS = {"etymological": "etymological", "pt_1973": "pt_1973", "ao1990_pt": "ao1990-pt",
              "br_1971": "br_1971", "ao1990_br": "ao1990-br"}
MODERN = ["ao1990", "br_1971", "pt_1973"]
MARKERS = {"etymological": ("etym", "etym-pattern"),
           "pt_1973": ("verbal-eem", "capital-month", "pre-ao90-pt"),
           "br_1971": ("pre-ao90-br", "trema"),
           "reforma_1911": ("reforma-1911",)}
COMPLETE_GOLD = {"silver_corpus", "silver_full", "relabel"}
MIN_UNITS = 15
FEATURELESS = 0.34


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split(group: str) -> str:
    return "cal" if int(hashlib.sha1(group.encode()).hexdigest(), 16) % 2 == 0 else "test"


def fetch_books(books: Path) -> None:
    books.mkdir(parents=True, exist_ok=True)
    for name in BOOKS:
        path = books / f"{name}.txt"
        if not path.exists():
            url = f"https://www.gutenberg.org/cache/epub/{name[2:]}/{name}.txt"
            req = urllib.request.Request(url, headers={"User-Agent": "desacordo-benchmark"})
            with urllib.request.urlopen(req) as resp:
                path.write_bytes(resp.read())


def units(args) -> Iterator[Tuple[str, str, str, str, str, List[str]]]:
    """Yield (source, grain, split, id, text, gold) for every unit."""
    for name in BOOKS:
        t = (args.books / f"{name}.txt").read_text(encoding="utf-8", errors="replace")
        s, e = t.find("*** START"), t.find("*** END")
        t = t[t.find("\n", s) + 1 if s >= 0 else 0: e if e >= 0 else None]
        src = "pg31347" if name == "pg31347" else "book13"
        gold = ["reforma_1911"] if src == "pg31347" else ["etymological"]
        sp = "test" if src == "pg31347" else split(name)
        for pi, par in enumerate(p for p in t.split("\n\n") if p.strip()):
            par = " ".join(par.split())
            yield src, "par", sp, f"{name}:{pi}", par, gold
            for si, sent in enumerate(SENT.split(par)):
                yield src, "sent", sp, f"{name}:{pi}.{si}", sent, gold

    for src, path in (("silver_corpus", BENCH / "silver_corpus.jsonl"),
                      ("silver_full", args.silver_full)):
        for line in open(path, encoding="utf-8"):
            row = json.loads(line)
            if src == "silver_corpus":
                cells = row["cells"]
            else:
                cells = {norm: row[col] for col, norm in HF_COLUMNS.items()}
            for col, text in cells.items():
                gold = sorted({FAMILY[c] for c, t in cells.items() if t == text})
                yield src, "row", split(row["id"]), f"{row['id']}:{col}", text, gold

    pre1911 = set(args.pre1911.read_text().split())
    for line in open(args.relabel, encoding="utf-8"):
        row = json.loads(line)
        gold = ["etymological"] if row["id"] in pre1911 else MODERN
        yield "relabel", "row", split(row["id"]), row["id"], row["text"], gold


def evidence_count(text: str, orth: Orthography, lex) -> int:
    """The number of distinct evidence tokens behind the label of ``orth``."""
    label = orth.era.value
    if label == "ao1990":
        words = {m.group().lower() for m in _WORD_RE.finditer(text)}
        return sum(w in lex.ao_pt_new2old or w in lex.ao_br_new2old for w in words)
    prefixes = MARKERS[label]
    return len({m.split(":", 1)[1] for m in orth.markers if m.split(":", 1)[0] in prefixes})


def judged(r: dict) -> bool:
    """Whether a unit's label can be judged against its gold set."""
    if r["label"] not in ("etymological", "reforma_1911", "pt_1973", "br_1971", "ao1990"):
        return False
    return (r["src"] in COMPLETE_GOLD
            or (r["src"] == "book13" and r["label"] in ("etymological", "reforma_1911"))
            or (r["src"] == "pg31347" and r["label"] == "reforma_1911"))


def featureless(r: dict) -> bool:
    return not r["markers"] and r["count"] == 0


def build_table(rows: List[dict]) -> Tuple[Dict[Cell, float], Dict[Cell, str]]:
    ok: collections.Counter = collections.Counter()
    n: collections.Counter = collections.Counter()
    for r in rows:
        if r["split"] == "cal" and judged(r) and not featureless(r):
            key = (r["src"], r["label"], min(r["count"], 2))
            n[key] += 1
            ok[key] += r["label"] in r["gold"]
    table: Dict[Cell, float] = {}
    source: Dict[Cell, str] = {}
    for (src, label, bucket), units_in_cell in sorted(n.items()):
        precision = ok[src, label, bucket] / units_in_cell
        cell = (label, bucket)
        if units_in_cell >= MIN_UNITS and precision < table.get(cell, 2.0):
            table[cell] = precision
            source[cell] = f"{src} {ok[src, label, bucket]}/{units_in_cell}"
    for bucket in (1, 2):
        if ("reforma_1911", bucket) not in table and ("etymological", bucket) in table:
            table["reforma_1911", bucket] = table["etymological", bucket]
            source["reforma_1911", bucket] = (f"provisional, the etymological cell; no source "
                                              f"has {MIN_UNITS} cal units")
    return {k: min(0.99, round(v, 2)) for k, v in table.items()}, source


def reforma_1911_units(rows: List[dict]) -> List[Tuple[str, str, str, int, int, int]]:
    """Every unit labelled reforma_1911: (source, grain, split, evidence count, correct, units)."""
    ok: collections.Counter = collections.Counter()
    n: collections.Counter = collections.Counter()
    for r in rows:
        if r["label"] == "reforma_1911":
            key = (r["src"], r["grain"], r["split"], min(r["count"], 2))
            n[key] += 1
            ok[key] += "reforma_1911" in r["gold"]
    return [k + (ok[k], v) for k, v in sorted(n.items())]


def calibration_error(rows: List[dict]) -> List[Tuple[str, str, int, float]]:
    """Expected calibration error (10 bins) on the test split, over judged units with evidence."""
    groups = collections.defaultdict(list)
    for r in rows:
        if r["split"] == "test" and judged(r) and not featureless(r):
            groups[r["src"], r["grain"]].append((r["conf"], float(r["label"] in r["gold"])))
    out = []
    for (src, grain), pairs in sorted(groups.items()):
        bins = collections.defaultdict(list)
        for p, y in pairs:
            bins[min(int(p * 10), 9)].append((p, y))
        gap = sum(abs(sum(p for p, _ in b) - sum(y for _, y in b)) for b in bins.values())
        ece = gap / len(pairs)
        out.append((src, grain, len(pairs), ece))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--books", type=Path, required=True)
    ap.add_argument("--silver-full", type=Path, required=True)
    ap.add_argument("--relabel", type=Path, required=True)
    ap.add_argument("--pre1911", type=Path, required=True)
    ap.add_argument("--labels", type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    fetch_books(args.books)
    inputs = [BENCH / "silver_corpus.jsonl", args.silver_full, args.relabel, args.pre1911]
    for path in inputs + [args.books / f"{name}.txt" for name in BOOKS]:
        print(f"input\t{sha256(path)}\t{path}")
    lex = get_lexicon()
    rows: List[dict] = []
    n_in: collections.Counter = collections.Counter()
    n_out: collections.Counter = collections.Counter()
    labels: List[str] = []
    for src, grain, sp, uid, text, gold in units(args):
        n_in[src, grain] += 1
        text = unicodedata.normalize("NFC", text)
        orth = detect(text, lex)
        if isinstance(orth, Orthography):
            r = {"label": orth.era.value, "count": evidence_count(text, orth, lex),
                 "markers": orth.markers, "conf": orth.confidence}
            label_id = orth.id
        else:
            r = {"label": "not-pt", "count": 0, "markers": [], "conf": orth.confidence}
            label_id = f"not-pt:{orth.lang}"
        r.update(src=src, grain=grain, split=sp, gold=gold)
        rows.append(r)
        n_out[src, grain] += 1
        labels.append(f"{src}\t{grain}\t{uid}\t{label_id}\n")
    if args.labels:
        args.labels.write_text("".join(labels), encoding="utf-8")

    print()
    for key in sorted(n_in):
        print(f"units\t{key[0]}\t{key[1]}\tin {n_in[key]}\tout {n_out[key]}")
    table, source = build_table(rows)
    print("\n# confidence table (label, evidence tokens): value  # source, correct/cal units")
    for (label, bucket), value in sorted(table.items()):
        print(f"(Era.{label.upper()}, {bucket}): {value:.2f},  # {source[label, bucket]}")
    print("\n# units labelled reforma_1911: source, grain, split, evidence tokens, correct/units")
    for src, grain, sp, bucket, correct, units_in_key in reforma_1911_units(rows):
        print(f"reforma_1911\t{src}\t{grain}\t{sp}\t{bucket}\t{correct}/{units_in_key}")
    print("\n# expected calibration error of detect().confidence, test split, units with evidence")
    for src, grain, n, ece in calibration_error(rows):
        print(f"ece\t{src}\t{grain}\t{n}\t{ece:.4f}")

    if not args.check:
        return 0
    # imported here so that the script also measures trees older than the table
    from desacordo_ortografico.detect import _CONFIDENCE
    committed = {(era.value, bucket): value for (era, bucket), value in _CONFIDENCE.items()}

    def cell(r: dict) -> float:
        return FEATURELESS if featureless(r) else committed[r["label"], min(r["count"], 2)]

    off = sum(r["conf"] != cell(r) for r in rows if r["label"] != "not-pt")
    print(f"\ncheck: table equals _CONFIDENCE: {table == committed}; "
          f"units whose confidence is not their table cell: {off}")
    return 0 if table == committed and off == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
