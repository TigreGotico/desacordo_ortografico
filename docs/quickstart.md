# Quickstart

## Install

```bash
pip install desacordo_ortografico
```

It depends only on [`tugalex`](https://github.com/TigreGotico/tugalex), which supplies
the bulk AO1990 word maps.

## Detect

`detect(text)` returns an `Orthography` (a Portuguese norm) or a `NotPortuguese` flag.

```python
from desacordo_ortografico import detect

r = detect("a pharmacia do theatro")
r.id           # 'etymological'
r.era          # Era.ETYMOLOGICAL
r.variant      # None  (variant-neutral)
r.confidence   # 0.99
r.markers      # ['etym-pattern:pharmacia', 'etym-pattern:theatro']
```

Detection works at the granularity orthography actually supports: `etymological`,
`pt_1973` / `br_1971` (pre-AO1990, European / Brazilian), and `ao1990-pt` / `ao1990-br`.
When no marker distinguishes the national variant, `variant` is `None`.

## Convert

```python
from desacordo_ortografico import convert

convert("a acção directa", "pre-ao1990-pt", "ao1990-pt")   # 'a ação direta'
convert("pharmacia", "etymological", "ao1990-br")          # 'farmácia'
convert("facto", "ao1990-pt", "ao1990-br")                 # 'fato'
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
res.lossless    # False  — restoring dropped consonants is lexical
res.warnings    # ['ao1990_pt (backward) is lexical/lossy: ...']

res = conv.convert("o facto", "ao1990-pt", "ao1990-br")
res.alternatives        # {'facto': ['facto', 'fato']}
conv.permitted_spellings("receção", "ao1990-pt")   # ['receção', 'recepção']
```

## Gotchas

- **Reverse conversion is lossy.** Toward newer norms it is well defined; toward older
  ones it relies on lexicons and is flagged via `lossless`/`warnings`.
- **AO1990 is two targets, not one.** Use `ao1990-pt` / `ao1990-br` (or pass `variant=`)
  to pick the European or Brazilian form of a dual word.
- **Sister languages are flagged, not converted.** See `docs/api.md`.
