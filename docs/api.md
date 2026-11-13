# API reference

## `detect(text, method="rules") -> Orthography | NotPortuguese`

Classify a text. Calls the sister-language guard first, then classifies. `method` is
`"rules"` (default, explainable), `"nb"`, or `"perceptron"` (the shipped learned models,
higher accuracy on sentence-length text, opt-in). Input is NFC-normalized.

`Orthography` fields: `era` (`Era`), `variant` (`Variant | None`), `confidence`
(`float`), `markers` (`list[str]`), `note` (`str`), `id` (`str`, a canonical norm id that
round-trips into `convert`), `is_portuguese` (`True`).

`NotPortuguese` fields: `lang`, `name`, `confidence`, `markers`, `convertible`
(`False`), `status`, `is_portuguese` (`False`).

## `convert(text, source, target, variant=None, features=None, pos_tags=None) -> str`

Convenience wrapper returning the converted string. `source`/`target` are norm ids or
aliases (see `eras`). `variant` (`"pt"`/`"br"`) biases dual-form selection.

`features` is a collection of names from `FEATURES`. Only those features apply. `None`
applies all of them. An unknown name raises `ValueError`.

`pos_tags` is a list of `(word, UPOS)` pairs for `text`, in the shape that
`tugatagger.TugaTagger(...).tag(text)` returns. desacordo does not tag text itself. The
pairs feed the 1911 accent guess only. They are matched to the words of `text` in order,
ignoring case, and a word with no matching pair is untagged.

Each edge of the norm graph is an ordered list of feature steps:

| Feature | What it changes | Edges |
| --- | --- | --- |
| `1911-word-map` | the curated 1911 word pairs (pharmacia -> farmácia) | reform_1911 |
| `1911-digraphs` | ph, th, rh -> f, t, r; y -> i | reform_1911 |
| `1911-geminates` | doubled consonants, except rr and ss | reform_1911 |
| `1911-accent-restore` | the graphic accent of a unique accented form (fosforo -> fósforo), see below | reform_1911 |
| `trema` | ü -> u | pt_1911_to_1945, ao1990_pt, ao1990_br |
| `subtonic-grave` | sòmente -> somente | accent_1973, accent_1971 |
| `base-iv` | the curated Base IV drop list | br_1911_to_1943, ao1990_pt |
| `ptbr-divergence` | the PT/BR divergence pairs (connosco -> conosco) | br_1911_to_1943, ptbr_divergence |
| `nasal-vowel` | é/ó -> ê/ô before a nasal | br_1911_to_1943, ptbr_divergence |
| `differential-1971` | the 1971 differential circumflex list (êle -> ele) | accent_1971 |
| `ao-map-consonant` | AO1990 map rows that change letters (acção -> ação) | ao1990_pt, ao1990_br |
| `ao-map-diacritic` | AO1990 map rows that change only accents (pêlo -> pelo) | ao1990_pt, ao1990_br |
| `ao-map-trema` | AO1990 map rows that drop only the trema | ao1990_pt, ao1990_br |
| `ao-map-join` | AO1990 map rows that fuse hyphenated parts (auto-retrato -> autorretrato) | ao1990_pt, ao1990_br |
| `ao-map-locution` | AO1990 map rows whose hyphens become spaces (fim-de-semana -> fim de semana) | ao1990_pt, ao1990_br |
| `differential` | the AO1990 differential accent list (pára -> para) | ao1990_pt, ao1990_br |
| `hyphen-lexical` | the AO1990 joined-compound list (manda-chuva -> mandachuva) | ao1990_pt, ao1990_br |
| `silent-cp` | the silent c/p rule for forms outside the map | ao1990_pt |
| `diphthong-accent` | éi/ói in a paroxytone (assembléia -> assembleia) | ao1990_pt, ao1990_br |
| `hiatus-accent` | ôo and êem (vôo -> voo) | ao1990_pt, ao1990_br |
| `prefix-rs` | prefix + r/s (auto-regulável -> autorregulável) | ao1990_pt, ao1990_br |
| `months` | month casing | every conversion |

The AO1990 word map owns the words it holds. When the class of a word's row is off, the
word stays as written, and the rules of that edge do not change it either.

The 1911 accent guess gives a bare word the accent of the one accented word that has
the same letters. A bare form that is itself a word stays as written (para, pára). So
does a regular inflection of a word, unless the context settles it:

| Bare form | Example | Takes the accent |
| --- | --- | --- |
| not a word and no inflection | fosforo -> fósforo | always |
| only a verb form | historia (historiar), continua (continuar) | after a determiner or a preposition (a sua história, de música); else when tagged NOUN or ADJ |
| only a plural in -s | pais (pai) | after a singular determiner: o país, os pais |
| a nominal form | antigas (antigo), tanta (tanto) | never |

A bare article (o, a, os, as) is also a clitic pronoun, so it counts as a determiner by
the variety of the target norm. For a European target it counts unless a word such as
não, que, já or quando stands right before it. For a Brazilian target it counts only at the
start of a sentence or clause or after a preposition. Elsewhere the bare article is the clitic
pronoun, and the next word is a verb. A pause ends the context: the word before a comma, a colon, a parenthesis or a dash decides nothing about the word after it. Brackets are no pause: they hold words an editor adds inside a quoted sentence. A tag decides only a word that this rule leaves
undecided: it never removes an accent the rule gives, and never adds one after a clitic
pronoun.

A capitalised word takes the accent of the common word with the same letters, anywhere
in a sentence, so names whose 1973 spelling carries an accent come back right (Árctico,
Atlântico, Ministério Público). The city names Coimbra and Roma share their letters with
an accented common word (coimbrã, romã), so they stay as written when capitalised:
"Fui a Roma." stays "Fui a Roma.", and "uma roma madura" gives "uma romã madura".

## `class OrthographyConverter`

- `convert(text, source, target, variant=None, features=None, pos_tags=None) -> ConversionResult`
- `permitted_spellings(word, norm) -> list[str]`: all officially valid spellings of a
  word in `norm` (two for AO1990 dual/divergence words, one otherwise).

### `ConversionResult`

`text`, `source`, `target`, `lossless` (`bool`), `warnings` (`list[str]`),
`alternatives` (`dict[str, list[str]]`).

## `detect_sister(text) -> NotPortuguese | None`

The guard alone, without the Portuguese classifier.

## Detection markers (`method="rules"`)

Detection markers are scored, not learned. They cover etymological evidence (`ph`,
`th`, `rh`, geminates, `sci`, irregular lemmas), pre-AO1990 evidence (old PT
silent-consonant forms, old BR accent/trema forms), AO1990 evidence, and PT/BR lean
(dual forms, the nasal-vowel alternation). `markers` lists what fired.

## `eras`

- `Era`: `ETYMOLOGICAL, REFORMA_1911, BR_1943, PT_1945, BR_1971, PT_1973, AO1990`.
- `Variant`: `PT, BR, NEUTRAL`.
- `Norm(era, variant)`: `.id`, `Norm.parse(str|Norm)`.
- `NORMS: dict[str, Norm]`, `EDGES: list[tuple]`, `find_path(src, dst) -> list[step]`.

## `lexicon`

`get_lexicon()` returns the shared `Lexicon`. It exposes `base_iv_keep/drop/dual`,
`dual_pt2br`, `differential_dropped/kept`, `hyphen_dropped`, `divergence_pt2br/br2pt`,
`reform1911_old2new`, `accent_71_73_old2new`, `sister_markers`, and the `tugalex`-backed
`ao_pt_old2new` / `ao_br_old2new` (with their inverses). `ao_pt_row_class` and
`ao_br_row_class` give the class of each AO1990 row (`ao_row_class(old, new)`). Every map has a reverse. AO1990
reverses come from the `tugalex` data and are authoritative where present.

## `ml`

`features(text)`, `train_naive_bayes(X, y)`, `train_perceptron_averaged(X, y)`, and the
`LinearModel` they return (`predict`, `predict_with_margin`, `scores`, `save`/`load`)
form a zero-dependency character-n-gram classifier. `get_detector_model("nb"|"perceptron")`
loads the shipped model used by `detect(method=...)`.

## CLI

```
desacordo detect [-v] TEXT...
desacordo convert --from NORM --to NORM [--variant pt|br] [-v] TEXT...
desacordo norms
```

`--stdin` reads the text from standard input. `-v` prints markers (detect) or
warnings/alternatives (convert).

---
[← Quickstart](quickstart.md) · [Home](../README.md) · [Orthographies →](orthographies.md)
