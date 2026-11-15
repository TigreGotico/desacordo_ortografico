# Quickstart

## Install

```bash
pip install desacordo_ortografico
```

It depends only on [`tugalex`](https://github.com/TigreGotico/tugalex) 2.4.9a1 or later,
which supplies the word list.

## Detect

`detect(text)` returns an `Orthography` (a Portuguese norm) or a `NotPortuguese` flag.

```python
from desacordo_ortografico import detect

r = detect("a pharmacia do theatro")
r.id           # 'etymological'
r.era          # Era.ETYMOLOGICAL
r.variant      # None  (variant-neutral)
r.confidence   # 0.99
r.markers      # ['etym:pharmacia', 'etym-pattern:theatro']
```

Detection works at the granularity orthography actually supports: `etymological`,
`reforma_1911` (the 1911 Portuguese spelling: tambêm, quási, armazêns, freqùente),
`pt_1973` / `br_1971` (pre-AO1990, European / Brazilian), and `ao1990-pt` / `ao1990-br`.
When no marker distinguishes the national variant, `variant` is `None`.

With the default rules, `confidence` is the held-out precision of the label for one, or
two or more, evidence tokens (`etym:pharmacia` and `etym-pattern:theatro` are two). The
`reforma_1911` values are provisional copies of the `etymological` values. An `ao1990`
result with a PT/BR lean marker and no AO1990 form gets 0.86. The
[API reference](api.md) gives the table and the corpora that measure it.

## Convert

```python
from desacordo_ortografico import convert

convert("a acção directa", "pre-ao1990-pt", "ao1990-pt")   # 'a ação direta'
convert("pharmacia", "etymological", "ao1990-br")          # 'farmácia'
convert("húmido", "ao1990-pt", "ao1990-br")                # 'úmido'
```

Norm names accept canonical ids (`ao1990-pt`), years (`1911`, `1990`), and aliases
(`pre-ao1990-pt`, `etymological`, `brazil-pre-90`). `desacordo norms` lists them.

## The full result

`OrthographyConverter.convert` returns a `ConversionResult` with reversibility info and
the dual-form alternatives that AO1990 permits:

```python
from desacordo_ortografico import OrthographyConverter
conv = OrthographyConverter()

res = conv.convert("a ação do diretor", "ao1990-pt", "pre-ao1990-pt")
res.text        # 'a acção do director'
res.lossless    # False  (restoring dropped consonants is lexical)
res.warnings    # ['ao1990_pt (backward) is lexical/lossy: ...']

res = conv.convert("o facto", "ao1990-pt", "ao1990-br")
res.alternatives        # {'facto': ['facto', 'fato']}
conv.permitted_spellings("receção", "ao1990-pt")   # ['receção', 'recepção']
```

## Gotchas

- **Reverse conversion is lossy.** Toward newer norms it is well defined. Toward older
  ones it relies on lexicons and is flagged via `lossless`/`warnings`.
- **AO1990 is two targets, not one.** Use `ao1990-pt` / `ao1990-br` (or pass `variant=`)
  to pick the European or Brazilian form of a dual word.
- **Sister languages are flagged, not converted.** See `docs/api.md`.
- **Input with no evidence defaults to `ao1990`.** Text with no listed form of any norm
  (empty, "a casa azul", or non-Portuguese that slips past the guard) returns `ao1990`
  with confidence 0.34. An AO1990 map form is evidence: "a ação" returns `ao1990` with
  0.96, although `markers` is empty. Check `confidence` to distinguish "confidently
  modern" from "no signal".

---
[Home](../README.md) · [API reference →](api.md)
