"""Regression test: the converter must reproduce an external authority's pre/post pairs.

`tests/data/ao1990_authority.jsonl` is a curated sample of pre-1990 European → AO1990
European spellings taken from portuguesaletra.com (scraped with `tools/`), spanning every
change type (silent c/p, open diphthong, hyphenation, differential accent). It guards
against regressions in the pt_1973 → ao1990-pt edge against an independent source.
"""
import json
import os

import pytest

from desacordo_ortografico import convert

HERE = os.path.dirname(__file__)
PAIRS = [json.loads(line) for line in
         open(os.path.join(HERE, "data", "ao1990_authority.jsonl"), encoding="utf-8")
         if line.strip()]


@pytest.mark.parametrize("row", PAIRS, ids=[r["old"] for r in PAIRS])
def test_pt_1973_to_ao1990_pt(row):
    # casefold: the converter preserves the input's (here lower) case, while the source
    # may capitalise a proper noun ("fula de Gabu") — that is not an orthographic change.
    assert convert(row["old"], "pt_1973", "ao1990-pt").casefold() == row["new"].casefold()
