# desacordo_ortografico

**Detect and convert between Portuguese orthographies**: the pre-1911 etymological
writing, the Reforma de 1911, the Brazilian (1943 / 1971) and European (1945 / 1973)
standards, and the *Acordo Ortográfico de 1990*, including the European and Brazilian
sub-variants that AO1990 deliberately keeps distinct.

This is a single-purpose library. It does orthography detection and conversion, and
nothing else.

- **Convert** any text between eight orthographic norms along a graph of historical
  reforms, with AO1990 dual-form (`facto`/`fato`) handling.
- **Detect** which orthography a text is written in: an explainable rule scorer, or two
  shipped zero-dependency learned classifiers (Naive Bayes / averaged perceptron).
- **Guard** against sister varieties (Mirandese, Galician, Barranquenho) that look like
  Portuguese but are not.
- A deterministic rule engine and curated, **sourced** exception lexicons. The AO1990
  word maps and the pre-1911 archaisms are rows of one spelling table,
  `data/spelling.json`, built from the [`tugalex`](https://github.com/TigreGotico/tugalex)
  lists. For pt-BR, `data/volp_ao1990_br.json` holds 1,796 spelling decisions, and each
  row cites its source. 1,628 rows quote the ABL *Vocabulário Ortográfico da Língua
  Portuguesa* (VOLP), 66 rows cite Priberam, and 102 rows record that no source decides
  the word.
- A **command-line tool** and a parallel silver benchmark corpus (written by language
  models, not checked by a person), also published on the
  [Hugging Face Hub](https://huggingface.co/datasets/TigreGotico/desacordo_ortografico).

## Why it is not a single find-and-replace

Portuguese spelling is a **(variant × era) matrix**, not one timeline. Two official
standards ran in parallel for most of the 20th century:

```
European / PALOP:  etymological → 1911 → 1945 → 1973 → AO1990 (PT)
Brazilian:         etymological → 1911 → 1943 → 1971 → AO1990 (BR)
```

AO1990 still admits **divergent** European/Brazilian spellings (`facto`/`fato`,
`António`/`Antônio`, `receção`/`recepção`). A conversion is therefore a *path* through a
graph of norms, applied edge by edge.

Some edges are clean regex rules (`ph→f`, trema abolition, the accent drops). Others are
irreducibly **lexical**: which silent consonant drops, which form a norm prefers. Those
are driven by curated, sourced data.

## Install

```bash
pip install desacordo_ortografico    # pulls in tugalex
```

## Use

```python
from desacordo_ortografico import detect, convert, OrthographyConverter

# --- detection -----------------------------------------------------------
detect("a pharmacia do theatro").id          # 'etymological'
detect("Tambêm sei!").id                      # 'reforma_1911'  (1911 spelling)
detect("o facto é óptimo").id                 # 'pt_1973'   (pre-AO1990, European)
detect("a idéia do vôo").id                   # 'br_1971'   (pre-AO1990, Brazilian)
detect("o Antônio é econômico").id            # 'ao1990-br'

# --- conversion ----------------------------------------------------------
convert("pharmacia", "etymological", "ao1990-br")          # 'farmácia'
convert("a acção directa", "pre-ao1990-pt", "ao1990-pt")   # 'a ação direta'
convert("freqüência", "pre-ao1990-br", "ao1990-br")        # 'frequência'
convert("húmido", "ao1990-pt", "ao1990-br")                # 'úmido'

# --- the full result: warnings + dual-form alternatives ------------------
conv = OrthographyConverter()
res = conv.convert("o facto é óptimo", "ao1990-pt", "ao1990-br")
res.text            # 'o facto é óptimo'  (the VOLP lists both forms of each word)
res.alternatives    # {'facto': ['facto', 'fato']}
conv.permitted_spellings("receção", "ao1990-pt")   # ['receção', 'recepção']
```

### Names toward pt-BR

AO1990 Base XXI lets a person, a firm or a brand keep the spelling of its name. Toward
`ao1990-br`, a word inside a sentence that starts with a capital, and is not in capitals
throughout, is a name. A name keeps
a form that the VOLP lists. The dual rule never gives a name a c or p that the source
did not write:

```python
convert("o setor e a Setor Norte", "ao1990-pt", "ao1990-br")
# 'o sector e a Setor Norte'
convert("o coletivo e o Coletivo Farra", "ao1990-pt", "ao1990-br")
# 'o colectivo e o Coletivo Farra'
```

The first word of a sentence and a text with no lowercase word give no case signal, so
they convert like any other word. So does a word in capitals: `o SETOR e o setor` gives
`o SECTOR e o sector`. See [`docs/api.md`](docs/api.md) for the `volp`
feature.

### Detection: rules or a learned model

`detect()` defaults to an explainable rule scorer. Two zero-dependency learned models
also ship: Naive Bayes and an averaged perceptron over character n-grams, sharing one
sparse-dot-product scoring rule. They score higher on sentence-length text. On held-out
5-fold cross-validation over the 6,645 renderings of the silver corpus, the compatible
accuracy is 96.4% for Naive Bayes, 95.6% for the perceptron and 92.6% for the rules
(`benchmark/train_detector.py`):

```python
detect("o Antônio era um génio econômico", method="nb")          # learned
detect("o Antônio era um génio econômico", method="perceptron")  # learned
detect("o Antônio era um génio econômico")                       # rules (default)
```

The guard runs first in every mode. Rule markers attach to a learned result for
explainability. The learned models have no `reforma_1911` class, so only the rules
return that label.

A rules `confidence` is the held-out precision of the label for one, or two or more,
evidence tokens, with two exceptions. The `reforma_1911` values are provisional copies of
the `etymological` values. An `ao1990` result with a PT/BR lean marker and no AO1990 form
gets 0.86: the Antônio example above returns `ao1990-br` with 0.86. A text with no
evidence gets 0.34. A learned
`confidence` comes from the model margin. [`docs/api.md`](docs/api.md) gives the table
and its sources.

### Sister-language guard

Mirandese, Galician (especially reintegrationist), and Barranquenho look like
Portuguese but are not. `detect()` recognizes and **flags** them rather than mangling
them:

```python
from desacordo_ortografico.guard import NotPortuguese
r = detect("umha cançom da naçom")
isinstance(r, NotPortuguese)   # True
r.name, r.convertible          # ('Galician', False)
```

## CLI

```bash
desacordo detect "a pharmacia do theatro"
desacordo convert --from pre-ao1990-pt --to ao1990-pt "a acção directa"
desacordo convert --from pre-ao1990-pt --to ao1990 --variant br "a recepção"
desacordo convert -v --from ao1990-pt --to ao1990-br "o facto"
desacordo detect --method nb "a idéia do vôo"
desacordo norms          # list the available orthographic norms
```

`--variant` picks the European or Brazilian AO1990 target: the example prints
`a recepção`, and `--variant pt` prints `a receção`. `-v` prints the lossy-edge warnings
and the dual-form alternatives (`alt: facto -> facto | fato`) to stderr. `--stdin` reads
the text from standard input.

## Norms

| id | reform | who / when |
|----|--------|------------|
| `etymological` | pre-1911 pseudo-etymological | — |
| `reforma_1911` | Reforma Ortográfica de 1911 | Portugal, 1911 |
| `br_1943` | Formulário Ortográfico de 1943 | Brazil (ABL) |
| `pt_1945` | Convenção Luso-Brasileira de 1945 | Portugal + PALOP |
| `br_1971` | accent mini-reform (Lei 5.765) | Brazil, 1971 |
| `pt_1973` | accent mini-reform (DL 32/73) | Portugal, 1973 |
| `ao1990-pt` / `ao1990-br` | Acordo Ortográfico de 1990 | all CPLP |

See [`docs/orthographies.md`](docs/orthographies.md) for the rule sets and sources.

## Reversibility

Forward conversion (toward newer norms) is well defined. Backward conversion is, for
several edges, **lexical and lossy**. Dropping a silent consonant or an accent discards
information no rule can recover. `ConversionResult.lossless` and `.warnings` report this
instead of silently guessing.

## Related projects

- [`tugalex`](https://github.com/TigreGotico/tugalex) — the word list this library
  reads, and the source of the AO1990 and archaism rows of its spelling table.

## License

Apache-2.0.
