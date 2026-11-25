#!/usr/bin/env python3
"""Build the feature chart of the documentation.

The chart shows, for each conversion feature, how many distinct words of the silver corpus
convert differently when that feature is off. Each word of the source rendering of a route
is converted alone once with every feature and once per feature with that feature removed.

    build_docs_plots.py --count   recount (slow, needs the package) and write the counts
    build_docs_plots.py --write   draw the SVG files from the counts
    build_docs_plots.py --check   fail when a committed SVG differs from its drawing

Only the standard library draws the chart, so --check needs no install.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"
COUNTS = ASSETS / "feature_words.json"
CORPUS = Path(__file__).resolve().parent.parent / "benchmark" / "silver_corpus.jsonl"
ROUTES = [
    ("etymological", "pt_1973", "etymological to pt_1973"),
    ("pt_1973", "ao1990-pt", "pt_1973 to ao1990-pt"),
    ("br_1971", "ao1990-br", "br_1971 to ao1990-br"),
]
THEMES = {
    "light": {"bg": "#ffffff", "ink": "#0b0b0b", "muted": "#52514e", "grid": "#d9d8d3",
              "series": ["#2a78d6", "#eb6834", "#1baf7a"]},
    "dark": {"bg": "#161514", "ink": "#f0efec", "muted": "#c3c2b7", "grid": "#3a3936",
             "series": ["#3987e5", "#d95926", "#199e70"]},
}
WIDTH, LEFT, RIGHT, TOP, ROW = 760, 170, 70, 96, 22
FONT = "font-family=\"DejaVu Sans, Verdana, sans-serif\""


def count() -> dict:
    import importlib

    from desacordo_ortografico.rules import words

    mod = importlib.import_module("desacordo_ortografico.convert")
    sentences = [json.loads(line)["cells"] for line in CORPUS.read_text(encoding="utf-8").splitlines()]
    conv = mod.OrthographyConverter()
    features = sorted(mod.FEATURES)
    out = {"routes": [r[2] for r in ROUTES], "rows": [], "features": {f: [0] * len(ROUTES) for f in features}}
    for k, (src, dst, _label) in enumerate(ROUTES):
        distinct = sorted({w for cells in sentences for w in words(cells[src])})
        out["rows"].append(len(distinct))
        for w in distinct:
            full = conv.convert(w, src, dst).text
            for f in features:
                if conv.convert(w, src, dst, features=mod.FEATURES - {f}).text != full:
                    out["features"][f][k] += 1
    return out


def nice_max(v: int) -> int:
    for step in (100, 200, 250, 500, 1000, 2000, 2500, 5000):
        if v <= step * 5:
            return -(-v // step) * step
    return v


def draw(data: dict, theme: str) -> str:
    t = THEMES[theme]
    items = sorted(((f, c) for f, c in data["features"].items() if sum(c)), key=lambda kv: -sum(kv[1]))
    top = max(sum(c) for _, c in items)
    axis = nice_max(top)
    step = axis // 5
    plot_w = WIDTH - LEFT - RIGHT
    height = TOP + ROW * len(items) + 36
    x = lambda v: LEFT + plot_w * v / axis  # noqa: E731
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
         f'viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="t d">',
         '<title id="t">Words changed by each conversion feature</title>',
         '<desc id="d">Stacked bars give, for each feature, the words of the spelling table that '
         'convert differently when the feature is off, split by route.</desc>',
         f'<rect width="{WIDTH}" height="{height}" fill="{t["bg"]}"/>',
         f'<text x="{LEFT - 150}" y="22" {FONT} font-size="14" font-weight="bold" fill="{t["ink"]}">'
         'Distinct words of the silver corpus that change when a feature is off</text>']
    for k, label in enumerate(data["routes"]):
        ly = 36 + k * 18
        o.append(f'<rect x="{LEFT - 150}" y="{ly}" width="12" height="12" fill="{t["series"][k]}"/>')
        o.append(f'<text x="{LEFT - 132}" y="{ly + 11}" {FONT} font-size="11" fill="{t["muted"]}">'
                 f'{label} ({data["rows"][k]:,} distinct words)</text>')
    for v in range(0, axis + 1, step):
        o.append(f'<line x1="{x(v):.1f}" y1="{TOP - 4}" x2="{x(v):.1f}" y2="{TOP + ROW * len(items)}" '
                 f'stroke="{t["grid"]}" stroke-width="1"/>')
        o.append(f'<text x="{x(v):.1f}" y="{TOP + ROW * len(items) + 16}" text-anchor="middle" {FONT} '
                 f'font-size="10" fill="{t["muted"]}">{v:,}</text>')
    for i, (name, counts) in enumerate(items):
        y = TOP + i * ROW
        o.append(f'<text x="{LEFT - 8}" y="{y + 14}" text-anchor="end" {FONT} font-size="11" '
                 f'fill="{t["ink"]}">{name}</text>')
        acc = 0
        for k, n in enumerate(counts):
            if n:
                o.append(f'<rect x="{x(acc):.1f}" y="{y + 3}" width="{x(acc + n) - x(acc):.1f}" '
                         f'height="{ROW - 7}" fill="{t["series"][k]}"/>')
            acc += n
        o.append(f'<text x="{x(acc) + 5:.1f}" y="{y + 14}" {FONT} font-size="10" '
                 f'fill="{t["muted"]}">{acc:,}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def targets(data: dict) -> dict[Path, str]:
    return {ASSETS / f"feature_words_{theme}.svg": draw(data, theme) for theme in THEMES}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--count", action="store_true", help="recount the words and write the counts file")
    mode.add_argument("--write", action="store_true", help="draw the SVG files from the counts")
    mode.add_argument("--check", action="store_true", help="fail when an SVG differs from its drawing")
    args = ap.parse_args()
    if args.count:
        COUNTS.write_text(json.dumps(count(), indent=1) + "\n", encoding="utf-8")
        print(f"wrote {COUNTS}")
        return 0
    data = json.loads(COUNTS.read_text(encoding="utf-8"))
    bad = 0
    for path, svg in targets(data).items():
        if args.write:
            path.write_text(svg, encoding="utf-8")
            print(f"wrote {path}")
        elif not path.exists() or path.read_text(encoding="utf-8") != svg:
            print(f"stale: {path}")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
