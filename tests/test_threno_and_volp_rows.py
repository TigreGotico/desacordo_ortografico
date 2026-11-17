"""Rows that a dictionary or the ABL VOLP decides against the tugalex lists.

- threno is the lament: Priberam gives "treno |ê| nome masculino. Canto fúnebre,
  lamentoso. = ELEGIA. Origem: latim threnus, -i, grego thrênos, -ou". Figueiredo 1913 has
  two headwords: "Treno,¹ m. Canto plangente; lamentação; elegia. (Lat. threnus)" and
  "Trenó, m. Espécie de vehículo sem rodas". The curated 1911 row threno -> treno puts treno
  on the word list, so the 1911 accent guess leaves it, and the backward pass gives threno
  for treno.
- conceptualmente: the VOLP lists "conceptual adj.2g.", and the search "concet" gives no
  row. data/volp_ao1990_br.json holds concetualmente -> conceptualmente.
- proativo: the VOLP lists "proativo adj." and "pró-ativo adj.", so the pt-BR row keeps
  proativo. Priberam gives "Grafia anterior ao Acordo Ortográfico de 1990: proactivo", so
  the pt_1973 row proactivo -> proativo holds the pt-PT spelling before 1990.
"""
import json
from pathlib import Path

import pytest

import desacordo_ortografico
from desacordo_ortografico import convert
from desacordo_ortografico.convert import FEATURES

_TABLE = Path(desacordo_ortografico.__file__).parent / "data" / "spelling.json"
_AFTER_1911 = ("reforma_1911", "pt_1945", "pt_1973", "br_1943", "br_1971", "ao1990-pt", "ao1990-br")


def _rows(form, era):
    with open(_TABLE, encoding="utf-8") as f:
        return [r for r in json.load(f)["rows"] if r["form"] == form and r["era"] == era]


def test_threno_is_a_curated_1911_row():
    (row,) = _rows("threno", "etymological")
    assert (row["value"], row["curated"]) == ("treno", True)


@pytest.mark.parametrize("target", _AFTER_1911)
def test_threno_gives_treno_on_every_edge(target):
    assert convert("threno", "etymological", target) == "treno"
    assert convert("threnos", "etymological", target) == "trenos"
    assert convert("o threno", "etymological", target) == "o treno"


def test_garrett_threno():
    # Garrett, Viagens na minha terra (Project Gutenberg 24401)
    assert convert("chorar o seu ultimo threno", "etymological",
                   "ao1990-pt") == "chorar o seu último treno"
    assert convert("Threnos sôbre Santarem", "etymological",
                   "ao1990-pt") == "Trenos sobre Santarem"


@pytest.mark.parametrize("target", _AFTER_1911)
def test_a_capital_threno_gives_treno(target):
    assert convert("Threno", "etymological", target) == "Treno"
    assert convert("THRENO", "etymological", target) == "TRENO"


@pytest.mark.parametrize("target", _AFTER_1911)
def test_a_bare_treno_stays_as_written(target):
    # Figueiredo 1913 lists Treno, the lament, as a headword of its own
    assert convert("treno", "etymological", target) == "treno"
    assert convert("trenos", "etymological", target) == "trenos"
    assert convert("Treno", "etymological", target) == "Treno"


def test_treno_goes_back_to_threno_and_trenó_stays():
    assert convert("treno", "reforma_1911", "etymological") == "threno"
    assert convert("treno", "ao1990-pt", "etymological") == "threno"
    assert convert("o trenó", "ao1990-pt", "etymological") == "o trenó"


def test_conceptualmente_keeps_its_consonant_in_pt_br():
    assert convert("conceptualmente", "br_1971", "ao1990-br") == "conceptualmente"
    assert convert("concetualmente", "ao1990-pt", "ao1990-br") == "conceptualmente"
    # VOLP: conceptual adj.2g.; no concetual. A form the VOLP lists stays as written
    # under every feature; only the volp feature writes the VOLP form of concetualmente
    assert convert("conceptualmente", "br_1971", "ao1990-br",
                   features=FEATURES - {"volp"}) == "conceptualmente"
    assert convert("concetualmente", "br_1971", "ao1990-br",
                   features=FEATURES - {"volp"}) == "concetualmente"


def test_proativo_stays_as_written():
    (row,) = _rows("proativo", "br_1971")
    assert row["value"] == "proativo"
    assert '"proativo adj." and "pró-ativo adj."' in row["source"]
    assert convert("proativo", "br_1971", "ao1990-br") == "proativo"


def test_proativo_was_proactivo_in_pt_pt():
    (row,) = _rows("proactivo", "pt_1973")
    assert row["value"] == "proativo"
    assert convert("proativo", "br_1971", "pt_1973") == "proactivo"
    assert convert("proativo", "ao1990-pt", "pt_1973") == "proactivo"
    assert convert("proactivo", "pt_1973", "ao1990-pt") == "proativo"
