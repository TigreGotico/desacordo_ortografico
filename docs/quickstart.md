# Quickstart

<!-- agent-hint
covers: how to install the package, detect a norm, convert a text and read the full result object
source: `desacordo_ortografico/detect.py:detect`, `desacordo_ortografico/convert.py:OrthographyConverter`, `desacordo_ortografico/guard.py`
generated: no
verify: d=$(mktemp -d) && sed '/^```/d' docs/quickstart.md > $d/q.txt && python -I -m doctest $d/q.txt
see: `api.md`, `orthographies.md`, `index.md`
-->

This page walks through the three things the package does: detect a norm, convert a text, and read the full result with its warnings. Run each Python example in a shell. Each one prints what the page shows.

## Install

```bash
pip install desacordo_ortografico
```

It depends only on [`tugalex`](https://github.com/TigreGotico/tugalex) 2.4.9a1 or later, which supplies the word list.

## Detect

`detect(text)` returns an `Orthography` (a Portuguese norm) or a `NotPortuguese` flag.

```python
>>> from desacordo_ortografico import detect
>>> r = detect("a pharmacia do theatro")
>>> r.id
'etymological'
>>> r.era
<Era.ETYMOLOGICAL: 'etymological'>
>>> r.variant is None
True
>>> r.confidence
0.99
>>> r.markers
['etym:pharmacia', 'etym-pattern:theatro']
```

Detection works at the granularity that orthography supports: `etymological`, `reforma_1911` (the 1911 Portuguese spelling: tambêm, quási, armazêns, freqùente), `pt_1973` and `br_1971` (pre-AO1990, European and Brazilian), and `ao1990-pt` and `ao1990-br`. When no marker distinguishes the national variant, `variant` is `None`.

With the default rules, `confidence` is the held-out precision of the label for one, or two or more, evidence tokens (`etym:pharmacia` and `etym-pattern:theatro` are two). The `reforma_1911` values are provisional copies of the `etymological` values. An `ao1990` result with a PT/BR lean marker and no AO1990 form gets 0.86. The [API reference](api.md) gives the table and the corpora that measure it.

Two learned models also ship, Naive Bayes and an averaged perceptron over character n-grams. Pass `method="nb"` or `method="perceptron"` to use one. They have no `reforma_1911` class, so only the rules return that label.

```python
>>> from desacordo_ortografico import detect
>>> detect("o Antônio era um génio econômico").id
'ao1990-br'
>>> detect("o Antônio era um génio econômico", method="nb").id
'br_1971'
>>> detect("o Antônio era um génio econômico", method="perceptron").id
'br_1971'
```

## Convert

```python
>>> from desacordo_ortografico import convert
>>> convert("a acção directa", "pre-ao1990-pt", "ao1990-pt")
'a ação direta'
>>> convert("pharmacia", "etymological", "ao1990-br")
'farmácia'
>>> convert("húmido", "ao1990-pt", "ao1990-br")
'úmido'
>>> convert("Tambêm êle quási sabia", "reforma_1911", "pt_1945")
'Também ele quase sabia'
>>> convert("Tambêm êle quási sabia", "reforma_1911", "br_1943")
'Também êle quase sabia'
```

Norm names accept canonical ids (`ao1990-pt`), years (`1911`, `1990`) and aliases (`pre-ao1990-pt`, `etymological`, `brazil-pre-90`). `desacordo norms` lists the canonical ids.

AO1990 has two targets. Pass `ao1990-pt` or `ao1990-br`, or pass `variant="pt"` or `variant="br"` with `ao1990`, to pick the European or the Brazilian form of a dual word.

```python
>>> from desacordo_ortografico import convert
>>> convert("a receção", "ao1990-pt", "ao1990", variant="br")
'a recepção'
```

## Read the full result

`OrthographyConverter.convert` returns a `ConversionResult` with the reversibility flag, the warnings and the dual-form alternatives that AO1990 permits.

```python
>>> from desacordo_ortografico import OrthographyConverter
>>> conv = OrthographyConverter()
>>> res = conv.convert("a ação do diretor", "ao1990-pt", "pre-ao1990-pt")
>>> res.text
'a acção do director'
>>> res.lossless
False
>>> res.warnings
['ao1990_pt (backward) is lexical/lossy: dropped accents/consonants are restored from a lexicon, not a rule']
>>> res = conv.convert("o facto", "ao1990-pt", "ao1990-br")
>>> res.alternatives
{'facto': ['facto', 'fato']}
>>> conv.permitted_spellings("receção", "ao1990-pt")
['receção', 'recepção']
```

## Names toward pt-BR

AO1990 Base XXI lets a person, a firm or a brand keep the spelling of its name. Toward `ao1990-br`, a word inside a sentence that starts with a capital, and is not in capitals throughout, is a name. A name keeps a form that the VOLP lists. The dual rule never gives a name a c or p that the source did not write.

```python
>>> from desacordo_ortografico import convert
>>> convert("o setor e a Setor Norte", "ao1990-pt", "ao1990-br")
'o sector e a Setor Norte'
>>> convert("o coletivo e o Coletivo Farra", "ao1990-pt", "ao1990-br")
'o colectivo e o Coletivo Farra'
>>> convert("o SETOR e o setor", "ao1990-pt", "ao1990-br")
'o SECTOR e o sector'
```

The first word of a sentence, a word in capitals and a text with no lowercase word give no case signal, so they convert like any other word.

## Sister languages

Mirandese, Galician and Barranquenho look like Portuguese but are not. `detect()` flags them and does not convert them.

```python
>>> from desacordo_ortografico import detect
>>> from desacordo_ortografico.guard import NotPortuguese
>>> r = detect("umha cançom da naçom")
>>> isinstance(r, NotPortuguese)
True
>>> r.name, r.convertible
('Galician', False)
```

## Command line

The `desacordo` command wraps the same calls. Each line below shows a command and what it prints.

```console
$ desacordo detect "a pharmacia do theatro"
etymological	confidence=0.99
  note: pre-1911 pseudo-etymological spelling (Greek digraphs, geminates)
$ desacordo detect -v "a pharmacia do theatro"
etymological	confidence=0.99
  note: pre-1911 pseudo-etymological spelling (Greek digraphs, geminates)
  markers: etym:pharmacia, etym-pattern:theatro
$ desacordo detect --method nb "a idéia do vôo"
br_1971	confidence=0.99
  note: pre-AO1990 Brazilian norm (trema and old accents: freqüência, idéia)
$ desacordo convert --from pre-ao1990-pt --to ao1990-pt "a acção directa"
a ação direta
$ desacordo convert --from pre-ao1990-pt --to ao1990 --variant br "a recepção"
a recepção
$ desacordo convert --from pre-ao1990-pt --to ao1990 --variant pt "a recepção"
a receção
$ desacordo convert -v --from ao1990-pt --to ao1990-br "o facto"
  alt: facto -> facto | fato
o facto
$ desacordo norms
ao1990-br
ao1990-pt
br_1943
br_1971
etymological
pt_1945
pt_1973
reforma_1911
```

`--variant` picks the European or the Brazilian AO1990 target. With `detect`, `-v` adds the markers to the output. With `convert`, `-v` prints the lossy-edge warnings and the dual-form alternatives to stderr. `--stdin` reads the text from standard input.

## Run the example scripts

The `examples/` folder holds five short scripts. Each one prints its result and needs no arguments.

| Script | It shows |
|---|---|
| `examples/01_detect.py` | detection of a sample from each norm |
| `examples/02_convert_ao90.py` | conversion between the pre-AO1990 norms and AO1990, with the lossy-edge warning |
| `examples/03_historical_1911.py` | one sentence carried along the European line |
| `examples/04_dual_forms.py` | the dual forms that AO1990 keeps apart |
| `examples/05_language_guard.py` | the guard that flags Mirandese, Galician and Barranquenho |

The third script prints this:

```console
$ python examples/03_historical_1911.py
Forward through the European line:
  (start)        A pharmacia tinha orthographia antiga.
  reforma_1911   A farmácia tinha ortografia antiga.
  pt_1945        A farmácia tinha ortografia antiga.
  pt_1973        A farmácia tinha ortografia antiga.
  ao1990-pt      A farmácia tinha ortografia antiga.

Single hop, etymological -> AO1990 (Brazilian):
  A farmácia tinha ortografia antiga.
```

## Reversibility

Forward conversion, toward newer norms, is well defined. Backward conversion is lexical and lossy on several edges, because dropping a silent consonant or an accent discards information that no rule can recover. `ConversionResult.lossless` and `.warnings` report this. From 1945 or 1943 back to 1911, only curated table rows apply: `cena` gives `scena` and `ciência` gives `sciência` (1911 Base XI).

## Gotchas

- Reverse conversion is lossy. Check `lossless` and `warnings`.
- Input with no evidence defaults to `ao1990`. Text with no listed form of any norm ("a casa azul", or non-Portuguese text that passes the guard) returns `ao1990` with confidence 0.34. An AO1990 map form is evidence: "a ação" returns `ao1990` with 0.96, although `markers` is empty. Check `confidence` to tell a confident result from a default.
- Some conversions of -ar verb forms are wrong. [Known limits](api.md#known-limits) lists them.

---
[Home](index.md) · [API reference →](api.md)
