# API reference

<!-- agent-hint
covers: every public name of the package with its signature and default, the detection markers and confidence table, and the known limits
source: `desacordo_ortografico/__init__.py`, `desacordo_ortografico/convert.py:convert`, `desacordo_ortografico/detect.py:_CONFIDENCE`, `desacordo_ortografico/lexicon.py`, `desacordo_ortografico/cli.py`
generated: no
verify: d=$(mktemp -d) && sed '/^```/d' docs/api.md > $d/a.txt && python -I -m doctest $d/a.txt
see: `features.md`, `quickstart.md`, `orthographies.md`, `index.md`
-->

This page lists the public names of `desacordo_ortografico` with their signatures and defaults. The conversion features have [their own page](features.md).

## Top-level names

The package exports these names from its top level:

```python
>>> import desacordo_ortografico as d
>>> d.__all__
['detect', 'convert', 'FEATURES', 'Orthography', 'NotPortuguese', 'detect_sister', 'OrthographyConverter', 'ConversionResult', 'Era', 'Variant', 'Norm', 'NORMS', 'EDGES', 'find_path', 'Lexicon', 'get_lexicon', '__version__']
```

`__version__` holds the package version. The other names have their own sections on this page, or on [the features page](features.md) for `FEATURES`.

## `detect(text, method="rules") -> Orthography | NotPortuguese`

Classify a text. Calls the sister-language guard first, then classifies. `method` is `"rules"` (default, explainable), `"nb"`, or `"perceptron"` (the shipped learned models, higher accuracy on sentence-length text, opt-in). Input is NFC-normalized.

`Orthography` fields: `era` (`Era`), `variant` (`Variant | None`), `confidence` (`float`, see below), `markers` (`list[str]`), `note` (`str`), `id` (`str`, a canonical norm id that round-trips into `convert`), `is_portuguese` (`True`).

With `method="rules"`, the label is one of `etymological` (pre-1911), `reforma_1911` (the Portuguese spelling of the Formulário Ortográfico of 1911), `pt_1973`, `br_1971`, `ao1990-pt`, `ao1990-br` and `ao1990`. `etymological` and `reforma_1911` have `variant` `None`. `br_1943` and `pt_1945` are norms of `convert` that `detect` does not return. The `"nb"` and `"perceptron"` models have no `reforma_1911` class.

With `method="rules"`, `confidence` is the held-out precision of the label for the number of distinct evidence tokens behind it: one, or two or more. Each value is the lowest precision over the measured populations: 13 pre-1911 Gutenberg books, `silver_corpus.jsonl`, `parallel.jsonl` of the Hugging Face dataset TigreGotico/desacordo_ortografico at revision 7049ddd (sha256 `61f1a10a...5f5026`), and 1,721 modern news sentences of which 50 were judged pre-1911 text. The news sentences are not in this repository. The values are the `_CONFIDENCE` table of `detect.py`, and `benchmark/confidence_table.py` measures them again from these files.

| Label | Evidence tokens | 1 token | 2 or more |
| --- | --- | --- | --- |
| `etymological` | listed pre-1911 forms (pharmacia, theatro) | 0.89 | 0.99 |
| `reforma_1911` | 1911 forms (tambêm, quási, armazêns, freqùente) | 0.89 | 0.99 |
| `pt_1973` | pre-AO1990 PT forms, `-êem`, a capital month | 0.79 | 0.92 |
| `br_1971` | pre-AO1990 BR forms, trema | 0.95 | 0.99 |
| `ao1990` | AO1990 map forms (ação, ótima) | 0.96 | 0.95 |

An `ao1990` result with no AO1990 form but with a PT/BR lean marker gets 0.86. A text with no evidence at all gets 0.34, because its label is only the default. With `"nb"` or `"perceptron"`, `confidence` comes from the model margin.

The `reforma_1911` values are provisional copies of the `etymological` values. The only dated text in the 1911 spelling is Eça de Queirós, Contos, Chardron 1913 (Gutenberg 31347), and it is held out, so no cal unit has a true `reforma_1911` label. On that book the label holds for 130 of 1,084 paragraphs. It holds for no unit of the 13 books printed before 1911, of the 1,721 news sentences, of the silver renderings or of the Formulário Ortográfico of 1943. A modern text that quotes a 1911 form also gets `reforma_1911` (the Acordos of 1945 and 1990 write "quase (em vez de quási)"), and so can OCR text that splits a Brazilian `-êm-` word (epidêm.io).

`NotPortuguese` fields: `lang`, `name`, `confidence`, `markers`, `convertible` (`False`), `status`, `is_portuguese` (`False`).

## `convert(text, source, target, variant=None, features=None, pos_tags=None) -> str`

Convenience wrapper returning the converted string. `source`/`target` are norm ids or aliases (see `eras`).

`variant` (`"pt"`/`"br"`) picks the AO1990 sub-norm when the target is an AO1990 norm: `convert("a receção", "ao1990-pt", "ao1990", variant="br")` gives `'a recepção'`. It takes the place of the variety in the target id, so `ao1990-pt` with `variant="br"` also gives `ao1990-br`. A target outside AO1990 ignores it. A value other than `"pt"` or `"br"` raises `ValueError` for every target.

`features` is a collection of names from `FEATURES`. Only those features apply. `None` applies all of them. An unknown name raises `ValueError`.

Toward an AO1990 target, the c/p form of a dual that the vocabulary of the target variety gives stays as written under every feature. Toward ao1990-br that is the form with the consonant of a VOLP dual in `data/volp_ao1990_br.json` (facto, contacto), and a bare form whose consonant form the VOLP rejects (cetro). The p of mpc, mpç and mpt counts as such a consonant, because AO1990 Base IV 1.º d) writes nc, nç and nt without it: sumptuoso beside suntuoso stays sumptuoso. Toward ao1990-pt it is the form with the consonant of a dual cell of the pt-PT map (sector, carácter). So `convert("o sector", "etymological", "ao1990-pt", features={"ao-map-consonant"})` gives `'o sector'`.

`pos_tags` is a list of `(word, UPOS)` pairs for `text`, in the shape that `tugatagger.TugaTagger(...).tag(text)` returns. desacordo does not tag text itself. The pairs feed the 1911 accent guess only. They are matched to the words of `text` in order, ignoring case, and a word with no matching pair is untagged.

Each edge of the norm graph is an ordered list of feature steps. [Conversion features](features.md) lists the 28 features with the edges that run them, a chart of the words each one changes, and the rules of the word maps, the foreign-word test and the 1911 accent guess.

## `class OrthographyConverter`

- `convert(text, source, target, variant=None, features=None, pos_tags=None) -> ConversionResult`
- `permitted_spellings(word, norm) -> list[str]`: all officially valid spellings of a word in `norm` (two for AO1990 dual/divergence words, one otherwise).

### `ConversionResult`

`text`, `source`, `target`, `lossless` (`bool`), `warnings` (`list[str]`), `alternatives` (`dict[str, list[str]]`).

## `detect_sister(text) -> NotPortuguese | None`

The guard alone, without the Portuguese classifier.

## Detection markers (`method="rules"`)

Detection markers are scored, not learned. They cover etymological evidence (the listed pre-1911 forms of the spelling table: pharmacia, theatro, collecção), pre-AO1990 evidence (old PT silent-consonant forms, old BR accent/trema forms), AO1990 evidence, and PT/BR lean (dual forms, the nasal-vowel alternation). `markers` lists what fired, except AO1990 evidence: an AO1990 map form counts toward `confidence` but adds no marker. A word that no list holds is no pre-1911 evidence, whatever its letters (the, Taylor). A listed form, except a whole curated word, inside a sentence whose word or part starts with a capital is read as a name and is no evidence ("A Moraci Sant'Anna chegou." is AO1990), except in the first word of a sentence or in a text with no lowercase word.

1911 evidence (marker `reforma-1911`) is a form of the Formulário Ortográfico of 1911 that Brazilian print of 1943 does not have: a polysyllable that ends in `-êm` or `-êns` (Bases XIV and XXV: tambêm, alguêm, armazêns, Belêm), `quási` (Base XXIV), and `qù` or `gù` (Base XLVI: freqùente, agùentar). porêm, alêm and an acute before `-mente` (Base XXXV: fácilmente) do not count, because books printed before 1911 have them. The third person plural of the compounds of ter and vir (contêm, provêm) does not count, because later norms keep its circumflex. The pronoun circumflex (êle, êste, dêle) does not count, because the Formulário Ortográfico of 1943, rule 14.ª, also writes it. A text with at least one 1911 form is `reforma_1911`, whatever its other markers. Brazilian print of 1943 to 1971 cannot have a 1911 form, because the 1943 Formulário writes também, quase and the trema (tranqüilo). Print in the 1911 spelling still has pre-1911 forms (emquanto, emfim), so a listed pre-1911 form does not outweigh a 1911 form.

## `eras`

- `Era`: `ETYMOLOGICAL, REFORMA_1911, BR_1943, PT_1945, BR_1971, PT_1973, AO1990`.
- `Variant`: `PT, BR, NEUTRAL`.
- `Norm(era, variant)`: `.id`, `Norm.parse(str|Norm)`.
- `NORMS: dict[str, Norm]`, `EDGES: list[tuple]`, `find_path(src, dst) -> list[step]`.

## `lexicon`

`get_lexicon()` returns the shared `Lexicon`. It exposes `base_iv_keep/drop/dual`, `dual_pt2br`, `differential_dropped/kept`, `hyphen_dropped`, `divergence_pt2br/br2pt`, `reform1911_old2new` (the curated 1911 pairs), `reform1911_forward` (every pre-1911 -> 1911 row), `reform1911_to_1945` and `reform1911_to_1943` (the 1911 -> pt_1945 and 1911 -> br_1943 rows: quási -> quase), `reform1911_from_1945` and `reform1911_from_1943` (the curated rows of those edges inverted: cena -> scena), `pre1911_forms`, `accent_71_73_old2new`, `sister_markers`, and the AO1990 maps `ao_pt_old2new` / `ao_br_old2new` (with their inverses). These maps read the spelling table `data/spelling.json`. `ao_pt_row_class` and `ao_br_row_class` give the class of each AO1990 row (`ao_row_class(old, new)`). `ao_br_volp` maps a pt-BR word to its form in the ABL VOLP, from `data/volp_ao1990_br.json`. `ao_br_volp_listed` holds the forms the VOLP lists, which decide the names toward pt-BR (see [orthographies](orthographies.md)). `hyphen_loanwords` maps `"pt"` and `"br"` to the forms of the `data/hyphen_loanwords.json` rows of that variety and their English plurals in -s. The prefix join reads it. `is_listed(word)` is true when the word, accents and all, is in the word list, or is a regular plural or feminine of a word in it. The `differential-1945` feature reads it. Every map has a reverse. AO1990 reverses come from the spelling table and are authoritative where present.

## `ml`

`features(text)`, `train_naive_bayes(X, y)`, `train_perceptron_averaged(X, y)`, and the `LinearModel` they return (`predict`, `predict_with_margin`, `scores`, `save`/`load`) form a zero-dependency character-n-gram classifier. `get_detector_model("nb"|"perceptron")` loads the shipped model used by `detect(method=...)`.

## CLI

```
desacordo detect [--method rules|nb|perceptron] [-v] TEXT...
desacordo convert --from NORM --to NORM [--variant pt|br] [-v] TEXT...
desacordo norms
```

`--stdin` reads the text from standard input. `-v` prints markers (detect) or warnings/alternatives (convert).

## Known limits

Four conversions of -ar verb forms give a wrong result, and the issue [#107](https://github.com/TigreGotico/desacordo_ortografico/issues/107) tracks them. The European first-person plural preterite in -ámos does not convert (`adoptámos` stays, where `adotámos` is right). The infinitives `retratar` and `coletar` convert where they must not: `retratar` gives `retractar` toward pt_1973, and `coletar` gives `colectar` toward ao1990-br. `decepcionada` gives `dececionada` toward ao1990-br, where the pt-BR norm keeps the consonant.

```python
>>> from desacordo_ortografico import convert
>>> convert("adoptámos", "pt_1973", "ao1990-pt")
'adoptámos'
>>> convert("retratar", "ao1990-pt", "pt_1973")
'retractar'
>>> convert("coletar", "ao1990-pt", "ao1990-br")
'colectar'
>>> convert("decepcionada", "pt_1973", "ao1990-br")
'dececionada'
```

The outputs above are wrong. They show what the code returns, so that a reader does not rely on them.

---
[← Quickstart](quickstart.md) · [Home](index.md) · [Conversion features →](features.md)
