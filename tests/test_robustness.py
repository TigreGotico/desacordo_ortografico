"""The public entry points must never crash on hostile or degenerate input."""
import pytest

from desacordo_ortografico import OrthographyConverter, convert, detect
from desacordo_ortografico.detect import Orthography
from desacordo_ortografico.guard import NotPortuguese

HOSTILE = [
    "",
    " ",
    "\n\t  \n",
    "123!?@#%",
    "😀🎉",
    "café",            # NFC
    "café",      # NFD: same word, combining acute
    "-",
    "--",
    "-abc-",
    "'",
    "d'água",
    "ПРИВЕТ こんにちhonestly",   # mixed scripts
    "ACÇÃO ÓPTIMO",            # all caps
    "facto.",
]


@pytest.fixture(scope="module")
def conv():
    return OrthographyConverter()


@pytest.mark.parametrize("text", HOSTILE)
def test_detect_never_raises(text):
    result = detect(text)
    assert isinstance(result, (Orthography, NotPortuguese))


@pytest.mark.parametrize("text", HOSTILE)
def test_convert_never_raises(text, conv):
    for src, dst in [
        ("etymological", "ao1990-pt"),
        ("ao1990-pt", "ao1990-br"),
        ("ao1990-pt", "etymological"),
        ("pre-ao1990-br", "ao1990-br"),
    ]:
        res = conv.convert(text, src, dst)
        assert isinstance(res.text, str)


@pytest.mark.parametrize("text", HOSTILE)
def test_permitted_spellings_never_raises(text, conv):
    assert isinstance(conv.permitted_spellings(text, "ao1990-pt"), list)


def test_convenience_convert_on_empty():
    assert convert("", "etymological", "ao1990-pt") == ""


def test_large_input_stays_linear(conv):
    # a big input must not trigger catastrophic regex backtracking
    text = "a acção óptima do director " * 4000  # ~110k chars
    res = conv.convert(text, "pre-ao1990-pt", "ao1990-pt")
    assert "ação" in res.text
    assert isinstance(detect(text), Orthography)
