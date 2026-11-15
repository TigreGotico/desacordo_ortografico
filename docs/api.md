# API reference

## `detect(text, method="rules") -> Orthography | NotPortuguese`

Classify a text. Calls the sister-language guard first, then classifies. `method` is
`"rules"` (default, explainable), `"nb"`, or `"perceptron"` (the shipped learned models,
higher accuracy on sentence-length text, opt-in). Input is NFC-normalized.

`Orthography` fields: `era` (`Era`), `variant` (`Variant | None`), `confidence`
(`float`, see below), `markers` (`list[str]`), `note` (`str`), `id` (`str`, a canonical
norm id that round-trips into `convert`), `is_portuguese` (`True`).

With `method="rules"`, `confidence` is the held-out precision of the label for the number
of distinct evidence tokens behind it: one, or two or more. Each value is the lowest
precision over the measured populations: 13 pre-1911 Gutenberg books, `silver_corpus.jsonl`,
`parallel.jsonl` of the Hugging Face dataset TigreGotico/desacordo_ortografico at revision
7049ddd (sha256 `61f1a10a...5f5026`), and 1,721 modern news sentences of which 50 were judged
pre-1911 text. The news sentences are not in this repository. The values are the
`_CONFIDENCE` table of `detect.py`, and `benchmark/confidence_table.py` measures them
again from these files.

| Label | Evidence tokens | 1 token | 2 or more |
| --- | --- | --- | --- |
| `etymological` | listed pre-1911 forms (pharmacia, theatro) | 0.89 | 0.99 |
| `pt_1973` | pre-AO1990 PT forms, `-êem`, a capital month | 0.79 | 0.92 |
| `br_1971` | pre-AO1990 BR forms, trema | 0.95 | 0.99 |
| `ao1990` | AO1990 map forms (ação, ótima) | 0.96 | 0.95 |

An `ao1990` result with no AO1990 form but with a PT/BR lean marker gets 0.86. A text with
no evidence at all gets 0.34, because its label is only the default. With `"nb"` or
`"perceptron"`, `confidence` comes from the model margin.

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
| `1911-word-map` | the curated 1911 word pairs and the tugalex archaisms list (pharmacia -> farmácia, comsigo -> consigo), see below | reform_1911 |
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
| `silent-cp` | the regular plural of an AO1990 map word that drops a c/p (actos -> atos), and back (atos -> actos) | ao1990_pt |
| `diphthong-accent` | éi/ói in a paroxytone (assembléia -> assembleia) | ao1990_pt, ao1990_br |
| `hiatus-accent` | ôo and êem (vôo -> voo) | ao1990_pt, ao1990_br |
| `prefix-rs` | prefix + r/s (auto-regulável -> autorregulável) | ao1990_pt, ao1990_br |
| `volp` | the ABL VOLP form of each pt-BR word that `data/volp_ao1990_br.json` holds (fato -> facto, aceção -> acepção) | every conversion to ao1990-br |
| `months` | month casing | every conversion |

The AO1990 word map owns the words it holds. When the class of a word's row is off, the
word stays as written, and the rules of that edge do not change it either. The 1911 word
map owns its words in the same way.

The 1911 word map joins the curated 1911 pairs and the rows of the tugalex archaisms list.
A tugalex row gives the modern pt-PT form, so a row enters only when its 1911 form is
known. Where the AO1990 pt-PT map lists the modern form, the 1911 form is the pre-AO1990
form of that map (architecto -> arquitecto). A row stays out when its modern form drops
a c or p that no table restores (affectando, AO1990 afetando), drops the initial sc that
1911 keeps (scintillar), is the bare form of a differential accent (pello, AO1990 pelo),
or drops an ê or ô of the archaic form (sêcco, 1911 sêco by Base XXVIII). Such a row
converts by the rules, as words outside the map do. For the other rows the modern form
stands for the 1911 form, and an accent that the archaic form does not show can still be
missing (elle gives ele, where 1911 writes êle).

Both varieties share the 1911 form, so a row also stays out when the Brazilian edges do
not turn the form it gives the 1911 map into its pt-BR form (character, pt-BR caráter).
This check tests only the rows whose form for the 1911 map differs from their pt-BR form.
For the other rows it only shows that the Brazilian edges keep the word, and it says
nothing about the 1911 form. Where the two maps hold the same word, the curated pair
decides. The backward pass reads the curated pairs only, because several archaic forms
can share one modern form.

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
pronoun, and the next word is a verb. A pause ends the context: the word before a comma, a colon, a parenthesis or a dash decides nothing about the word after it. Brackets are no pause: they hold remarks an author adds inside a transcribed text. A tag decides only a word that this rule leaves
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

Detection markers are scored, not learned. They cover etymological evidence (the
listed pre-1911 forms of the 1911 word map and of the tugalex archaisms list: pharmacia,
theatro, collecção), pre-AO1990 evidence (old PT silent-consonant forms, old BR
accent/trema forms), AO1990 evidence, and PT/BR lean (dual forms, the nasal-vowel
alternation). `markers` lists what fired, except AO1990 evidence: an AO1990 map form
counts toward `confidence` but adds no marker. A word that no list holds is no pre-1911
evidence, whatever its letters (the, Taylor). A form of the tugalex archaisms list inside a
sentence whose word or part starts with a capital is read as a name and is no evidence ("A Moraci
Sant'Anna chegou." is AO1990), except in the first word of a sentence or in a text with
no lowercase word.

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
`ao_br_row_class` give the class of each AO1990 row (`ao_row_class(old, new)`).
`ao_br_volp` maps a pt-BR word to its form in the ABL VOLP, from `data/volp_ao1990_br.json`. Every map has a reverse. AO1990
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
