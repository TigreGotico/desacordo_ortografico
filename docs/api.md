# API reference

## `detect(text, method="rules") -> Orthography | NotPortuguese`

Classify a text. Calls the sister-language guard first, then classifies. `method` is
`"rules"` (default, explainable), `"nb"`, or `"perceptron"` (the shipped learned models;
higher accuracy on sentence-length text, opt-in). Input is NFC-normalised.

`Orthography` fields: `era` (`Era`), `variant` (`Variant | None`), `confidence`
(`float`), `markers` (`list[str]`), `note` (`str`), `id` (`str`, a canonical norm id that
round-trips into `convert`), `is_portuguese` (`True`).

`NotPortuguese` fields: `lang`, `name`, `confidence`, `markers`, `convertible`
(`False`), `status`, `is_portuguese` (`False`).

## `convert(text, source, target, variant=None) -> str`

Convenience wrapper returning the converted string. `source`/`target` are norm ids or
aliases (see `eras`). `variant` (`"pt"`/`"br"`) biases dual-form selection.

## `class OrthographyConverter`

- `convert(text, source, target, variant=None) -> ConversionResult`
- `permitted_spellings(word, norm) -> list[str]` — all officially valid spellings of a
  word in `norm` (two for AO1990 dual/divergence words, one otherwise).

### `ConversionResult`

`text`, `source`, `target`, `lossless` (`bool`), `warnings` (`list[str]`),
`alternatives` (`dict[str, list[str]]`).

## `detect_sister(text) -> NotPortuguese | None`

The guard alone, without the Portuguese classifier.

## Detection markers (`method="rules"`)

Detection markers are scored, not learned. Etymological evidence (`ph`, `th`, `rh`,
geminates, `sci`, irregular lemmas), pre-AO1990 evidence (old PT silent-consonant forms,
old BR accent/trema forms), AO1990 evidence, and PT/BR lean (dual forms, the nasal-vowel
alternation). `markers` lists what fired.

## `eras`

- `Era` — `ETYMOLOGICAL, REFORMA_1911, BR_1943, PT_1945, BR_1971, PT_1973, AO1990`.
- `Variant` — `PT, BR, NEUTRAL`.
- `Norm(era, variant)` — `.id`, `Norm.parse(str|Norm)`.
- `NORMS: dict[str, Norm]`, `EDGES: list[tuple]`, `find_path(src, dst) -> list[step]`.

## `lexicon`

`get_lexicon()` returns the shared `Lexicon`. Exposes `base_iv_keep/drop/dual`,
`dual_pt2br`, `differential_dropped/kept`, `hyphen_dropped`, `divergence_pt2br/br2pt`,
`reform1911_old2new`, `accent_71_73_old2new`, `sister_markers`, and the `tugalex`-backed
`ao_pt_old2new` / `ao_br_old2new` (+ their inverses). Every map has a reverse; AO1990
reverses come from the `tugalex` data and are authoritative where present.

## `ml`

`features(text)`, `train_naive_bayes(X, y)`, `train_perceptron_averaged(X, y)`, and the
`LinearModel` they return (`predict`, `predict_with_margin`, `scores`, `save`/`load`) —
a zero-dependency character-n-gram classifier. `get_detector_model("nb"|"perceptron")`
loads the shipped model used by `detect(method=...)`.

## CLI

```
desacordo detect [-v] TEXT...
desacordo convert --from NORM --to NORM [--variant pt|br] [-v] TEXT...
desacordo norms
```

`--stdin` reads the text from standard input. `-v` prints markers (detect) or
warnings/alternatives (convert).
