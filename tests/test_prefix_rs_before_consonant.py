"""AO1990 Base XVI 2º a): no hyphen after a vowel prefix when the second element starts
with r or s, and the r or s doubles.

Every example of the clause has a vowel after the doubled letter: antirreligioso,
antissemita, contrarregra, contrassenha, cosseno, extrarregular, infrassom, minissaia,
biorritmo, biossatélite, eletrossiderurgia, microssistema, microrradiografia. The
digraphs rr and ss stand only between vowels. The tugalex regional dictionary (Portal da
Língua Portuguesa) has no word with rr or ss before a consonant. So the hyphen goes and
the letter stays single before a consonant: the gold rows p10-018 and d00691 of
gold_full.jsonl (Hugging Face dataset TigreGotico/desacordo_ortografico) write
anti-spam in pt_1973 and br_1971, and antispam in ao1990-pt and ao1990-br.
"""
import gzip
import re
from pathlib import Path

import pytest
import tugalex

from desacordo_ortografico import convert, rules


def test_dictionary_never_writes_rr_or_ss_before_a_consonant():
    path = Path(tugalex.__file__).parent / "data" / "regional_dict.csv.gz"
    with gzip.open(path, "rt", encoding="utf-8") as f:
        words = {line.split(",", 1)[0] for line in f if not line.startswith(("#", "word,"))}
    assert len(words) > 50000
    assert not [w for w in words if re.search(r"(rr|ss)[^aeiouáàâãéêíóôõúü]", w)]


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
