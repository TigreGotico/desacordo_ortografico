"""Command-line interface: ``desacordo detect`` and ``desacordo convert``."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .convert import OrthographyConverter
from .detect import detect
from .eras import NORMS
from .guard import NotPortuguese


def _read_text(args: argparse.Namespace) -> str:
    if getattr(args, "stdin", False) or not args.text:
        return sys.stdin.read().strip()
    return " ".join(args.text)


def _cmd_detect(args: argparse.Namespace) -> int:
    text = _read_text(args)
    result = detect(text)
    if isinstance(result, NotPortuguese):
        print(f"not-portuguese\t{result.lang}\t{result.name}\tconfidence={result.confidence}")
        if result.status:
            print(f"  status: {result.status}")
        if result.markers:
            print(f"  markers: {', '.join(result.markers[:8])}")
        return 0
    print(f"{result.id}\tconfidence={result.confidence}")
    if result.note:
        print(f"  note: {result.note}")
    if args.verbose and result.markers:
        print(f"  markers: {', '.join(result.markers[:12])}")
    return 0


def _cmd_convert(args: argparse.Namespace) -> int:
    text = _read_text(args)
    conv = OrthographyConverter()
    res = conv.convert(text, args.source, args.target, variant=args.variant)
    print(res.text)
    if args.verbose:
        if not res.lossless:
            for w in res.warnings:
                print(f"  warning: {w}", file=sys.stderr)
        for word, forms in res.alternatives.items():
            print(f"  alt: {word} -> {' | '.join(forms)}", file=sys.stderr)
    return 0


def _cmd_norms(_args: argparse.Namespace) -> int:
    for nid in sorted(NORMS):
        print(nid)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="desacordo",
        description="Detect and convert between Portuguese orthographies.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("detect", help="classify which orthography a text uses")
    d.add_argument("text", nargs="*", help="text to classify (or use --stdin)")
    d.add_argument("--stdin", action="store_true", help="read text from stdin")
    d.add_argument("-v", "--verbose", action="store_true")
    d.set_defaults(func=_cmd_detect)

    c = sub.add_parser("convert", help="convert text between two norms")
    c.add_argument("--from", dest="source", required=True, help="source norm (see `norms`)")
    c.add_argument("--to", dest="target", required=True, help="target norm")
    c.add_argument("--variant", default=None, choices=["pt", "br"],
                   help="bias dual-form selection (facto/fato)")
    c.add_argument("text", nargs="*", help="text to convert (or use --stdin)")
    c.add_argument("--stdin", action="store_true", help="read text from stdin")
    c.add_argument("-v", "--verbose", action="store_true", help="print warnings/alternatives")
    c.set_defaults(func=_cmd_convert)

    n = sub.add_parser("norms", help="list the available orthographic norms")
    n.set_defaults(func=_cmd_norms)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
