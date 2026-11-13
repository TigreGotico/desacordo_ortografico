"""AO1990 Base XVI 2º a): no hyphen after a vowel prefix when the second element starts
with r or s, and the r or s doubles.

Every example of the clause has a vowel after the doubled letter: antirreligioso,
antissemita, contrarregra, contrassenha, cosseno, extrarregular, infrassom, minissaia,
biorritmo, biossatélite, eletrossiderurgia, microssistema, microrradiografia. The
digraphs rr and ss stand only between vowels. The tugalex AO1990 maps have no word with
rr or ss before a consonant. So the hyphen goes and the letter stays single before a
consonant: the gold rows p10-018 and d00691 of
gold_full.jsonl (Hugging Face dataset TigreGotico/desacordo_ortografico) write
anti-spam in pt_1973 and br_1971, and antispam in ao1990-pt and ao1990-br.
"""
import re

import pytest
from tugalex import TugaLexicon

from desacordo_ortografico import convert, rules


@pytest.mark.parametrize("variant", ["ao_pt", "ao_br"])
def test_ao_map_never_writes_rr_or_ss_before_a_consonant(variant):
    words = set()
    for old, new in getattr(TugaLexicon(), variant).items():
        words.add(old)
        words.update(new if isinstance(new, list) else [new])
    doubled = [w for w in words if re.match(r"(anti|contra|auto|micro|infra|extra|mini)(rr|ss)", w)]
    assert len(doubled) > 100
    assert not [w for w in words if re.search(r"(rr|ss)[^aeiouáàâãéêíóôõúü\s-]", w)]


@pytest.mark.parametrize("target", ["ao1990-pt", "ao1990-br"])
def test_consonant_after_the_r_or_s_joins_without_doubling(target):
    source = "pre-ao1990-pt" if target == "ao1990-pt" else "pre-ao1990-br"
    assert convert("um filtro anti-spam", source, target) == "um filtro antispam"


@pytest.mark.parametrize("old,new", [
    ("anti-religioso", "antirreligioso"),
    ("contra-senha", "contrassenha"),
    ("micro-sistema", "microssistema"),
])
def test_base_xvi_examples_still_double(old, new):
    assert rules.ao1990_hyphen_rs(old) == new


def test_one_letter_base_does_not_double():
    # no vowel follows the s, so it stays single (Base XVI 2º a examples all have one)
    assert rules.ao1990_hyphen_rs("anti-s") == "antis"
