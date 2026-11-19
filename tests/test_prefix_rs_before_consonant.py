"""AO1990 Base XVI 2º a): no hyphen after a vowel prefix when the second element starts
with r or s, and the r or s doubles.

Every example of the clause has a vowel after the doubled letter: antirreligioso,
antissemita, contrarregra, contrassenha, cosseno, extrarregular, infrassom, minissaia,
biorritmo, biossatélite, eletrossiderurgia, microssistema, microrradiografia. The
digraphs rr and ss stand only between vowels. The AO1990 maps of data/spelling.json have
no word with rr or ss before a consonant. So the hyphen goes and the letter stays single
before a consonant: the silver rows p10-018 and d00691 of silver_full.jsonl (Hugging Face dataset TigreGotico/desacordo_ortografico) write
anti-spam in pt_1973 and br_1971, and antispam in ao1990-pt and ao1990-br.
"""
import json
import re
from pathlib import Path

import pytest

import desacordo_ortografico
from desacordo_ortografico import convert, rules

_TABLE = Path(desacordo_ortografico.__file__).parent / "data" / "spelling.json"


@pytest.mark.parametrize("era", ["pt_1973", "br_1971"])
def test_ao_map_never_writes_rr_or_ss_before_a_consonant(era):
    words = set()
    with open(_TABLE, encoding="utf-8") as f:
        for row in json.load(f)["rows"]:
            if row["era"] == era:
                words.add(row["form"])
                words.update(row["value"].split("|"))
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


@pytest.mark.parametrize("era", ["pt_1973", "br_1971"])
def test_no_ao_row_joins_r_or_s_without_doubling(era):
    # a prefix that ends in a vowel, a hyphen, then r or s and a vowel
    checked, joins = 0, []
    with open(_TABLE, encoding="utf-8") as f:
        for row in json.load(f)["rows"]:
            m = re.fullmatch(r"(\w*[aeiou])-([rs][aeiouáéíóúâêô]\w*)", row["form"])
            if row["era"] == era and m:
                checked += 1
                joins += [v for v in row["value"].split("|") if v == m[1] + m[2]]
    assert checked > 200
    assert joins == []


@pytest.mark.parametrize("source,target", [("pt_1973", "ao1990-pt"), ("br_1971", "ao1990-br")])
def test_neo_republicano_doubles_the_r(source, target):
    # The VOP (Portal da Língua Portuguesa) lists "neorrepublicano - nome masculino" (lemma
    # 174210) and "neorrepublicano - adjetivo" (lemma 177767), and has no neorepublicano.
    assert convert("o partido neo-republicano", source, target) == "o partido neorrepublicano"
    assert convert("o partido neorrepublicano", target, source) == "o partido neo-republicano"
