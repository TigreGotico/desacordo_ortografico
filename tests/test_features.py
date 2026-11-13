"""The ``features=`` allowlist of :func:`convert`.

Each case word is a standard example of its reform. The expected spelling comes from the
reform text cited on the row, not from the library.
"""
import json
from pathlib import Path

import pytest

from desacordo_ortografico import FEATURES, OrthographyConverter, convert

P = ("etymological", "ao1990-pt")
B = ("etymological", "ao1990-br")
X = ("ao1990-pt", "ao1990-br")

# feature -> (path, old word, new word)
CASES = {
    # Reforma de 1911: ph -> f, th -> t, geminates reduced, graphic accents
    "1911-word-map": (P, "pharmacia", "farmácia"),
    "1911-digraphs": (P, "theatro", "teatro"),
    "1911-geminates": (P, "commissão", "comissão"),
    "1911-accent-restore": (P, "fosforo", "fósforo"),
    # Convenção de 1945 for Portugal, AO1990 Base XIV 1º for Brazil: no trema
    "trema": (P, "lingüiça", "linguiça"),
    # Decreto-Lei 32/73: no subtonic grave accent
    "subtonic-grave": (P, "sòmente", "somente"),
    # AO1990 Base IV 1º c): mute c dropped
    "ao-map-consonant": (P, "acção", "ação"),
    # AO1990 Base IX 9º: pêlo loses its differential accent
    "ao-map-diacritic": (P, "pêlo", "pelo"),
    # AO1990 Base XIV 1º
    "ao-map-trema": (B, "freqüência", "frequência"),
    # AO1990 Base XVI 1º b): prefix + r doubles the r
    "ao-map-join": (P, "auto-retrato", "autorretrato"),
    # AO1990 Base XV 6º: locutions lose the hyphens
    "ao-map-locution": (P, "fim-de-semana", "fim de semana"),
    # AO1990 Base IX 9º: pára (verb) loses its accent
    "differential": (P, "pára", "para"),
    # AO1990 Base XV 1º obs.: mandachuva is written joined
    "hyphen-lexical": (P, "manda-chuva", "mandachuva"),
    # AO1990 Base IV 1º c)
    "base-iv": (P, "acções", "ações"),
    "silent-cp": (P, "afectiva", "afetiva"),
    # AO1990 Base IX 3º: éi in a paroxytone loses the accent
    "diphthong-accent": (P, "assembléia", "assembleia"),
    # AO1990 Base IX 8º: ôo loses the accent
    "hiatus-accent": (P, "vôo", "voo"),
    # AO1990 Base XVI 1º b)
    "prefix-rs": (P, "auto-regulável", "autorregulável"),
    # AO1990 Base XIX 1º: months take a lower-case initial
    "months": (P, "em Janeiro", "em janeiro"),
    # AO1990 Base IV 1º c): conosco is the Brazilian form
    "ptbr-divergence": (X, "connosco", "conosco"),
    # AO1990 Base IX 2º: académico / acadêmico
    "nasal-vowel": (X, "académica", "acadêmica"),
    # Lei 5.765/1971: no differential circumflex
    "differential-1971": (B, "êle", "ele"),
}


def test_every_feature_has_a_case():
    assert set(CASES) == FEATURES


@pytest.mark.parametrize("feature", sorted(CASES))
def test_feature_alone_applies(feature):
    path, old, new = CASES[feature]
    assert convert(old, *path, features={feature}) == new


@pytest.mark.parametrize("feature", sorted(CASES))
def test_feature_alone_changes_only_its_word(feature):
    path = CASES[feature][0]
    words = [old for p, old, _ in CASES.values() if p == path]
    expected = [new if f == feature else old for f, (p, old, new) in CASES.items() if p == path]
    assert convert(" , ".join(words), *path, features={feature}) == " , ".join(expected)


@pytest.mark.parametrize("path", [P, B, X])
def test_no_features_changes_nothing(path):
    text = " , ".join(old for p, old, _ in CASES.values() if p == path)
    assert convert(text, *path, features=()) == text


def test_unknown_feature_raises():
    with pytest.raises(ValueError, match="no-such-feature"):
        convert("acção", *P, features={"trema", "no-such-feature"})


def test_a_bare_string_raises():
    with pytest.raises(TypeError):
        convert("acção", *P, features="trema")


def test_none_equals_every_feature_on_the_gold_corpus():
    conv = OrthographyConverter()
    gold = Path(__file__).parent.parent / "benchmark" / "gold_corpus.jsonl"
    rows = [json.loads(line)["cells"] for line in gold.open(encoding="utf-8")]
    assert len(rows) == 1329
    for cells in rows:
        for src, text in cells.items():
            for dst in cells:
                if dst != src:
                    default = conv.convert(text, src, dst)
                    explicit = conv.convert(text, src, dst, features=FEATURES)
                    assert (default.text, default.warnings) == (explicit.text, explicit.warnings)
