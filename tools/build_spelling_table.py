#!/usr/bin/env python3
"""Build ``desacordo_ortografico/data/spelling.json`` from the tugalex spelling lists.

    python tools/build_spelling_table.py [--curated-json reform_1911_irregular.json] [--out PATH]

The table took its rows from four sources, in this order:

1. the curated pre-1911 -> 1911 pairs (``curated`` true). ``--curated-json`` reads them,
   their sources and the comment of each group from ``data/reform_1911_irregular.json``
   of a desacordo_ortografico release that ships it, such as 0.2.1a1. Without it the
   script keeps the curated rows, ``_sources`` and ``_groups`` of the table at ``--out``.
   :func:`decide_1911` then applies the rows that the Formulário of 1911 decides;
2. the rows of the tugalex ``archaisms.csv`` list. A row gives its modern pt-PT form, and
   that form can also carry a change made after 1911, so :func:`archaism_row_class` sorts
   the rows. A ``1911`` or ``ao1990-map`` row becomes a pre-1911 -> 1911 row when the
   Brazilian edges turn its 1911 form into its pt-BR form. Every other row, and every row
   of :data:`TWO_1911_FORMS`, gets rows for its AO1990 forms only;
3. the tugalex AO1990 pt-PT list (``acordo_ortografico_pt_PT.csv``), as pt_1973 rows;
4. the tugalex AO1990 pt-BR list (``acordo_ortografico_pt_BR.csv``), as br_1971 rows. A
   cell of :data:`VOLP_AO_BR` takes the form of the ABL VOLP instead;
5. the rows on the edges out of 1911, :data:`ROWS_OUT_OF_1911`: the 1911 words that no
   rule of those edges reaches, and the words that the backward pass of those edges reads,
   each with the clause of the Acordo Ortográfico of 1945, the Bases of 1931 or the
   Formulário Ortográfico of 1943 that gives its later form. The rows of
   :data:`INVERTED_OUT_OF_1911` are curated.

The script ran once, with the tugalex release that desacordo_ortografico pins as its
floor. People edit the table by hand from then on, like the other data files.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from functools import cached_property
from typing import Dict, List, Tuple, Union

from tugalex import TugaLexicon

from desacordo_ortografico import rules
from desacordo_ortografico.convert import FEATURES, OrthographyConverter
from desacordo_ortografico.lexicon import Lexicon, deaccent

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE = os.path.join(HERE, "..", "desacordo_ortografico", "data", "spelling.json")
COLUMNS = ["form", "era", "target", "value", "curated", "source"]
ABOUT = (
    "The spelling facts that convert() and detect() read. Each row maps form, written in "
    "the norm era, to value in the norm target. source names the entry of _sources that the "
    "row comes from, and for a curated pre-1911 row the group of _groups. A dual AO1990 cell joins "
    "its two forms with '|', in source order. curated is true for the pairs that the "
    "backward pass of their edge inverts. detect() weighs a curated pre-1911 form double. "
    "A pre-1911 form whose 1911 "
    "form no source decides, or that has two 1911 forms (mallogro gives the noun malôgro and "
    "the verb malogro), has rows for its AO1990 forms only. "
    "The reforma_1911 values do not always have the accents of the 1911 print. A curated "
    "value has its AO1990 diacritics (elle gives ele, where the 1911 print writes êle). "
    "Where the European and Brazilian norms differ only by an open or closed vowel before a "
    "nasal (anónimo, anônimo; cómodo, cômodo), the value is the European form, and the "
    "Brazilian edge derives ê and ô by rule. A value from the tugalex archaisms list is its "
    "modern pt-PT form (comsigo gives consigo), or its pre-AO1990 form where the AO1990 "
    "pt-PT map lists the modern form (architecto gives arquitecto). The 1911 reform kept the c and p of -ct- and -pt- words such as acto, óptimo, "
    "director and afecto: affecto gives afecto in 1911, and only the AO1990 edge gives afeto. "
    "A reforma_1911 row gives the pt_1945 or br_1943 form of a 1911 word that no rule of the "
    "edge reaches (quási gives quase), or of a 1911 word that the backward pass of the edge "
    "reads (cena gives scena). "
    "tools/build_spelling_table.py built the rows with tugalex 2.4.9a1."
)

#: The 1911 JSON writes two of its sources without accents; the table cites them as the
#: works print them.
REFORM_1911 = "Reforma Ortográfica de 1911 (Portaria de 1 de setembro de 1911), comissão de Gonçalves Viana"
CITATIONS = {
    "Reforma Ortografica de 1911 (Portaria de 1 de Setembro de 1911), comissao de Goncalves Viana": REFORM_1911,
    "Candido de Figueiredo, Novo Diccionario da Lingua Portuguesa (1913)":
        "Cândido de Figueiredo, Novo Diccionário da Língua Portuguesa (1913)",
}

#: The tugalex lists that the rows other than the curated pairs come from.
TUGALEX_SOURCES = ["tugalex archaisms.csv", "tugalex acordo_ortografico_pt_PT.csv",
                   "tugalex acordo_ortografico_pt_BR.csv"]
#: The norms that the edges out of 1911 lead to, and the rows of those edges: the 1911
#: form, the target norm, the form in that norm and the clause.
ACORDO_1945 = "Acordo Ortográfico de 1945 (Decreto n.º 35 228, de 8 de Dezembro de 1945)"
FORMULARIO_1943 = "Formulário Ortográfico de 1943 (Academia Brasileira de Letras)"
ACORDO_1931 = ("Acordo Ortográfico de 1931 (Academia das Ciências de Lisboa e Academia Brasileira "
               "de Letras, 30 de Abril de 1931)")
_TER_VIR_1945 = ('Base XX: "têm e vêm, [...] são de emprego exclusivo na escrita corrente, '
                 'preterindo assim as formas dissilábicas têem e vêem"')
_TAM_1943 = ('28., Observação 2.ª: "Com o ditongo nasal ão se escrevem os monossílabos, tônicos '
             'ou não, e os polissílabos oxítonos: cão, dão, grão, não, quão, são, tão"')
_TER_VIR_1943 = ('7.ª, Observação 2.ª: "A 3.ª pessoa do plural do presente do indicativo dos '
                 'verbos ter, vir e seus compostos recebe acento circunflexo no e da sílaba '
                 'tônica: (êles) contêm, (elas) convêm, (êles) têm, (elas) vêm, etc."')
_BASE_XI_1911 = ('1911 form, Base XI: "É conservado o grupo inicial sc, das seguintes palavras e '
                 'seus derivados e afins, em que o s é mudo: scena, sciência"')
_SC_1931 = f'§ 1.º Eliminar: "4.º O s do grupo inicial: ciência, ciática"; {_BASE_XI_1911}'
_SC_1943 = (f'19.: "Elimina-se o s do grupo inicial sc: celerado, cena, cenografia, ciência, '
            f'cientista, cindir, cintilar, ciografia, cisão, etc."; {_BASE_XI_1911}')
ROWS_OUT_OF_1911 = [
    ("quási", "pt_1945", "quase", f'{ACORDO_1945} (Base IX: "quase (em vez de quási)")'),
    ("tam", "pt_1945", "tão", f'{ACORDO_1945} (Base XIII: "tão (não tam)")'),
    ("quam", "pt_1945", "quão", f'{ACORDO_1945} (Base XIII: "quão (não quam)")'),
    ("teem", "pt_1945", "têm", f"{ACORDO_1945} ({_TER_VIR_1945})"),
    ("veem", "pt_1945", "vêm", f"{ACORDO_1945} ({_TER_VIR_1945})"),
    ("scetro", "pt_1945", "ceptro", f'{ACORDO_1945} (Base VI, 2.°: "Conservam-se não apenas nos '
                                     f'casos em que são invariavelmente proferidos [...], mas '
                                     f'também naqueles em que só se proferem em Portugal ou só '
                                     f'no Brasil [...]: [...] assumptível, assumptivo, ceptro, '
                                     f'consumpção [...] (p interior geralmente proferido no '
                                     f'Brasil, mas predominantemente mudo em Portugal)")'),
    ("quási", "br_1943", "quase", f'{FORMULARIO_1943} (33.: "Assim, pois, devem ser inscritos '
                                   f'vocábulos como: [...] pior, quase, quepe")'),
    ("tam", "br_1943", "tão", f"{FORMULARIO_1943} ({_TAM_1943})"),
    ("quam", "br_1943", "quão", f"{FORMULARIO_1943} ({_TAM_1943})"),
    ("teem", "br_1943", "têm", f"{FORMULARIO_1943} ({_TER_VIR_1943})"),
    ("veem", "br_1943", "vêm", f"{FORMULARIO_1943} ({_TER_VIR_1943})"),
    # an inverted initial-sc rule would give scenoura from cenoura, so the backward pass
    # reads these rows. The decree of 1945: the accord of 1931 "foi aprovado e mandado
    # executar, em Portugal pela portaria n.o 7:117, de 27 de Maio do mesmo ano"
    ("scena", "pt_1945", "cena", f"{ACORDO_1931} ({_SC_1931})"),
    ("sciência", "pt_1945", "ciência", f"{ACORDO_1931} ({_SC_1931})"),
    ("scena", "br_1943", "cena", f"{FORMULARIO_1943} ({_SC_1943})"),
    ("sciência", "br_1943", "ciência", f"{FORMULARIO_1943} ({_SC_1943})"),
]
#: The rows on the edges out of 1911 that the backward pass of the edge inverts. Base XI
#: keeps the sc of scena and sciência.
INVERTED_OUT_OF_1911 = frozenset({"scena", "sciência"})
#: The curated pre-1911 pairs that the Formulário Ortográfico of 1911 decides. scena is a
#: 1911 spelling of Base XI, so it leaves the pre-1911 map, and sciencia gives the 1911
#: sciência of Base XI. The edges out of 1911 give cena and ciência by
#: :func:`rules.drop_initial_sc` and by rows that the backward pass reads.
#:
#: The pre-1911 row kilo -> quilo stays. Base I, Excepção 2.ª permits kilo and writes quilo
#: as the better form: "Continuam em uso os símbolos W, para denotar o Oeste, e K como
#: abreviatura de unidade métrica, e tambêm na forma international kilo, que todavia se
#: poderá escrever quilo; tanto mais, que o k é um grosseiro êrro nesta palavra, pois o
#: correspondente termo grego se escreve com χ, e não κ." quilo is also the only 1911
#: spelling of the chyle (chylo -> quilo).
SPELLINGS_OF_1911 = frozenset({"scena"})
DECIDED_1911 = {"sciencia": ("sciência", "initial_sc")}
GROUPS_1911 = {
    "initial_sc": 'Base XI keeps the initial sc: "É conservado o grupo inicial sc, das seguintes '
                  'palavras e seus derivados e afins, em que o s é mudo: scena, sciência, scetro, '
                  'scéptico, scisma, scisão, sciático, scintilar, scelerado". The value has the '
                  'accent of the 1911 print.',
}
#: The pre-1911 forms with two 1911 forms. The 1911 circumflex marks the closed vowel of a
#: noun against the open vowel of the verb form, so mallogro is the noun malôgro or the verb
#: form malogro, and a 1911 row would hold one of them.
TWO_1911_FORMS = {
    "mallogro": f'{REFORM_1911} (Base XXVIII: "Assim se diferençarão rêgo, substantivo, e rego, '
                f'verbo"; Base XXXIV: "pois dizemos malograr, malôgro")',
}
VOLP_ABL = "Vocabulário Ortográfico da Língua Portuguesa (Academia Brasileira de Letras)"
#: The pt-BR AO1990 cells whose form the ABL VOLP decides against tugalex. tugalex has the
#: cell "co-fator, co-factor" -> "cofator, cofactor", and the table holds it as co-factor ->
#: cofator|cofactor. The VOLP entry is, to its end: "cofator adj. s.m.". It has no entry
#: for co-fator, cofactor or co-factor (the searches "co-fat", "cofact" and "co-fact" give no
#: row). So pt-BR writes cofator only, and co-factor gives cofator, as co-fator does.
#: The pt-PT row cofactor -> cofator agrees with the Vocabulário Ortográfico do Português
#: (Portal da Língua Portuguesa), whose entry is, to its end: "cofator - nome masculino
#: co · fa · tor singular cofator plural cofatores Flexiona como : dor variante AO :
#: cofactor ( Brasil)". For pt-BR the ABL VOLP decides, and it lists no cofactor.
#: For bissector, fotelectricidade, idielectricidade and dactilozóide the tugalex list gives
#: one form, and the VOLP lists both forms as headwords, so the cell holds both. The first
#: form stays first, so the single-form map does not change.
VOLP_AO_BR = {
    "co-factor": ("cofator", '"cofator adj. s.m."'),
    "bissector": ("bissetor|bissector", '"bissetor (ô) adj. s.m." and "bissector (ô) adj. s.m."'),
    "fotelectricidade": ("foteletricidade|fotelectricidade",
                         '"foteletricidade s.f." and "fotelectricidade s.f."'),
    "idielectricidade": ("idieletricidade|idielectricidade",
                         '"idieletricidade s.f." and "idielectricidade s.f."'),
    "dactilozóide": ("dactilozoide|datilozoide",
                     '"dactilozoide (ó) adj. s.m." and "datilozoide (ó) adj. s.m."'),
}
Row = Dict[str, Union[str, bool]]
Curated = Tuple[List[Row], List[str], Dict[str, str]]

#: The classes of a tugalex archaism row, see :func:`archaism_row_class`.
ARCHAISM_ROW_CLASSES = ("1911", "ao1990-map", "ao1990-cp", "ao1990-differential", "sc", "circumflex")

#: A Base IV 1º sequence of the AO1990 after a vowel: cc, cç, ct, pc, pç or pt.
_CP_SEQUENCE = re.compile(r"(?<=[aeiou])[cp][cçt]")


def archaism_row_class(archaic: str, modern: str, lex: Lexicon) -> str:
    """Classify a tugalex archaism row (``archaic`` -> its modern pt-PT form ``modern``)
    by the reform that its modern form rests on.

    ``1911``: no check below finds a post-1911 change, so the modern form stands for the
    1911 form (comsigo -> consigo, phosphoro -> fósforo). The checks do not find every
    accent: Base VII of 1911 writes "êle", and the row elle -> ele is in this class.
    ``ao1990-map``: the AO1990 pt-PT word map lists the modern form, so the 1911 form is the
    pre-AO1990 form of that map (architecto -> arquiteto, before AO1990 arquitecto).
    ``ao1990-differential``: the modern form is the bare form of a differential accent
    that the AO1990 dropped (pello -> pelo, before AO1990 pêlo).
    ``ao1990-cp``: the modern form lacks the c or p of a Base IV 1º sequence that the
    archaic form keeps after the regular 1911 rules, and the AO1990 map does not list it.
    1911 Base VIII drops such a consonant where it is silent (auctor -> autor), Base IX
    keeps it where it changes the vowel before it (affectando -> afectando, AO1990
    afetando), and no table here tells the two apart.
    ``sc``: the archaic form starts with the group sc and the modern form does not. Base
    XI of 1911 keeps that group (scena, sciência), and later accords drop it (cintilar).
    ``circumflex``: the archaic form has more ê or ô than the modern form. Base XXVIII
    of 1911 marks the closed e or o of a homograph ("rêgo, substantivo, e rego,
    verbo"), later laws drop that accent (sêcco -> seco, 1911 sêco), and no table here
    gives the 1911 form of every such row.

    Only the ``1911`` and ``ao1990-map`` rows can enter the 1911 word map.
    """
    if archaic.startswith("sc") and not modern.startswith("sc"):
        return "sc"
    if modern in lex.differential_dropped.values() or modern in lex.differential_restore:
        return "ao1990-differential"
    if modern in lex.ao_pt_new2old:
        return "ao1990-map"
    regular = rules.reform_1911_geminates(rules.reform_1911_digraphs(archaic))
    if len(_CP_SEQUENCE.findall(deaccent(regular))) > len(_CP_SEQUENCE.findall(deaccent(modern))):
        return "ao1990-cp"
    if _circumflexes(archaic) > _circumflexes(modern):
        return "circumflex"
    return "1911"


def _circumflexes(word: str) -> int:
    """The number of ê and ô in ``word``, the closed vowels of Base XXVIII."""
    return word.count("ê") + word.count("ô")


def row(form: str, era: str, target: str, value: str, curated: bool, source: str) -> Row:
    return dict(zip(COLUMNS, (form, era, target, value, curated, source)))


def curated_from_json(path: str) -> Curated:
    """The pairs of each group of the 1911 JSON, lowercased, with its sources and the
    comment of each group. A key seen again keeps its first position and takes the later
    value, as the dict of the old loader did. Each pair cites the first source of the file,
    the Portaria of 1911, and its group. Sources are written as in ``CITATIONS``."""
    pairs: Dict[str, Row] = {}
    comments: Dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    sources = [CITATIONS.get(s, s) for s in data["_sources"]]
    assert sources[0] == REFORM_1911, sources[0]
    for group, entries in data.items():
        if group.startswith("_") or not isinstance(entries, dict):
            continue
        comments[group] = entries["_comment"]
        for k, v in entries.items():
            if k.startswith("_") or not isinstance(v, str):
                continue
            pairs[k.lower()] = row(k.lower(), "etymological", "reforma_1911", v.lower(), True,
                                   f"{sources[0]} ({group})")
    return list(pairs.values()), sources + TUGALEX_SOURCES + [ACORDO_1945, FORMULARIO_1943], comments


def decide_1911(curated: List[Row]) -> List[Row]:
    """The curated rows after the decisions of :data:`SPELLINGS_OF_1911` and
    :data:`DECIDED_1911`."""
    out = []
    for r in curated:
        if r["form"] in SPELLINGS_OF_1911:
            continue
        if r["form"] in DECIDED_1911:
            value, group = DECIDED_1911[r["form"]]
            r = {**r, "value": value, "source": f"{REFORM_1911} ({group})"}
        out.append(r)
    return out


def curated_from_table(path: str) -> Curated:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    sources = data["_sources"] + [s for s in (ACORDO_1945, FORMULARIO_1943) if s not in data["_sources"]]
    curated = [r for r in data["rows"] if r["curated"] and r["era"] == "etymological"]
    return curated, sources, data["_groups"]


def ao_rows(tuga: TugaLexicon) -> List[Row]:
    """The raw cells of both tugalex AO1990 lists, in file order."""
    out = []
    for cells, path, era, target in ((tuga.ao_pt, tuga.ao_pt_path, "pt_1973", "ao1990-pt"),
                                     (tuga.ao_br, tuga.ao_br_path, "br_1971", "ao1990-br")):
        for old, news in cells.items():
            assert not any("|" in n for n in news), (old, news)
            value, source = "|".join(news), f"tugalex {os.path.basename(path)}"
            if era == "br_1971" and old in VOLP_AO_BR:
                value, quote = VOLP_AO_BR[old]
                source = f"{VOLP_ABL} ({quote})"
            out.append(row(old, era, target, value, False, source))
    return out


def dump(table: Dict[str, object]) -> str:
    """The table as JSON with one list item or one key per line, so that a change to a row
    is a one-line diff."""
    def block(open_: str, close: str, items: List[str]) -> str:
        return open_ + "\n    " + ",\n    ".join(items) + "\n  " + close

    parts = []
    for key, value in table.items():
        if isinstance(value, list):
            text = block("[", "]", [json.dumps(v, ensure_ascii=False) for v in value])
        elif isinstance(value, dict):
            text = block("{", "}", [f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}"
                                    for k, v in value.items()])
        else:
            text = json.dumps(value, ensure_ascii=False)
        parts.append(f"  {json.dumps(key)}: {text}")
    return "{\n" + ",\n".join(parts) + "\n}\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--curated-json",
                        help="reform_1911_irregular.json of a desacordo release that ships it, "
                             "such as 0.2.1a1")
    parser.add_argument("--out", default=TABLE)
    args = parser.parse_args()

    tuga = TugaLexicon()
    curated, sources, groups = (curated_from_json(args.curated_json) if args.curated_json
                                else curated_from_table(args.out))
    curated = decide_1911(curated)
    groups = {**groups, **GROUPS_1911}
    sources = sources + [s for s in (ACORDO_1931, VOLP_ABL) if s not in sources]
    ao = ao_rows(tuga)

    class SourceLexicon(Lexicon):
        """The lexicon with the curated pairs and the AO1990 lists, before the archaisms."""

        @cached_property
        def _spelling(self) -> List[Row]:
            return curated + ao

    lex = SourceLexicon()
    edges = OrthographyConverter(lex)._edges

    def brazilian(word: str) -> str:
        for name in ("br_1911_to_1943", "accent_1971", "ao1990_br"):
            word = edges[name].forward.apply(word, FEATURES)
        return word

    notes = {}
    with open(tuga.archaisms_path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            notes[r["archaic"]] = f"tugalex archaisms.csv ({r['notes']})"

    curated_forms = {r["form"] for r in curated}
    to_1911, modern_only = [], []
    for archaic, modern in tuga.archaic_words.items():
        row_class = archaism_row_class(archaic, modern, lex)
        form = {"1911": modern, "ao1990-map": lex.ao_pt_new2old.get(modern)}.get(row_class)
        if archaic in TWO_1911_FORMS:
            form = None
        if form is not None and brazilian(form) == tuga.archaic_words_br[archaic]:
            if archaic not in curated_forms:
                to_1911.append(row(archaic, "etymological", "reforma_1911", form, False, notes[archaic]))
        elif archaic not in curated_forms:
            source = TWO_1911_FORMS.get(archaic, notes[archaic])
            modern_only.append(row(archaic, "etymological", "ao1990-pt", modern, False, source))
            br = tuga.archaic_words_br[archaic]
            if br != modern:
                modern_only.append(row(archaic, "etymological", "ao1990-br", br, False, source))

    out_of_1911 = [row(form, "reforma_1911", target, value, form in INVERTED_OUT_OF_1911, source)
                   for form, target, value, source in ROWS_OUT_OF_1911]
    rows = curated + to_1911 + modern_only + out_of_1911 + ao
    # one row per line, so that a change to a row is a one-line diff
    assert all(any(r["source"].startswith(s) for s in sources) for r in rows)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(dump({"_about": ABOUT, "_sources": sources, "_groups": groups, "rows": rows}))
    print(f"archaisms in {len(tuga.archaic_words)}: to 1911 {len(to_1911)}, "
          f"AO1990 forms only {len({r['form'] for r in modern_only})}, "
          f"curated {len([a for a in tuga.archaic_words if a in curated_forms])}")
    print(f"rows written {len(rows)}: curated {len(curated)}, archaisms {len(to_1911) + len(modern_only)}, "
          f"out of 1911 {len(out_of_1911)}, AO1990 {len(ao)}")


if __name__ == "__main__":
    main()
