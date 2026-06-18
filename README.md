# desacordo_ortografico

**Detect and convert between Portuguese orthographies** — the pre-1911 etymological
writing, the Reforma de 1911, the Brazilian (1943 / 1971) and European (1945 / 1973)
standards, and the *Acordo Ortográfico de 1990*, including the European and Brazilian
sub-variants that AO1990 deliberately keeps distinct.

This is a single-purpose library: it does orthography detection and conversion, and
nothing else. The bulk AO1990 word data is reused from
[`tugalex`](https://github.com/TigreGotico/tugalex); on top of it this package adds a
deterministic rule engine, the historical-reform edges, the Base IV exception lexicons,
and a marker-based detector.

## Why it is not a single find-and-replace

Portuguese spelling is a **(variant × era) matrix**, not one timeline. Two official
standards ran in parallel for most of the 20th century:

```
European / PALOP:  etymological → 1911 → 1945 → 1973 → AO1990 (PT)
Brazilian:         etymological → 1911 → 1943 → 1971 → AO1990 (BR)
```

and AO1990 still admits **divergent** European/Brazilian spellings (`facto`/`fato`,
`António`/`Antônio`, `receção`/`recepção`). A conversion is therefore a *path* through a
graph of norms, applied edge by edge. Some edges are clean regex rules (`ph→f`,
trema abolition, the accent drops); others are irreducibly **lexical** (which silent
consonant drops, which form a norm prefers) and are driven by curated, sourced data.

## Install

```bash
pip install desacordo_ortografico    # pulls in tugalex
```

## Use

```python
from desacordo_ortografico import detect, convert, OrthographyConverter

# --- detection -----------------------------------------------------------
detect("a pharmacia do theatro").id          # 'etymological'
detect("o facto é óptimo").id                 # 'pt_1973-pt' (pre-AO1990, European)
detect("a idéia do vôo").id                   # 'br_1971-br' (pre-AO1990, Brazilian)
detect("o Antônio é econômico").id            # 'ao1990-br'

# --- conversion ----------------------------------------------------------
convert("pharmacia", "etymological", "ao1990-br")          # 'farmácia'
convert("a acção directa", "pre-ao1990-pt", "ao1990-pt")   # 'a ação direta'
convert("freqüência", "pre-ao1990-br", "ao1990-br")        # 'frequência'
convert("facto", "ao1990-pt", "ao1990-br")                 # 'fato'

# --- the full result: warnings + dual-form alternatives ------------------
conv = OrthographyConverter()
res = conv.convert("o facto é óptimo", "ao1990-pt", "ao1990-br")
res.text            # 'o fato é óptimo'  (óptimo isn't a divergence, stays)
res.alternatives    # {'facto': ['facto', 'fato']}
conv.permitted_spellings("receção", "ao1990-pt")   # ['receção', 'recepção']
```

### Detection: rules or a learned model

`detect()` defaults to an explainable rule scorer. Two zero-dependency learned models
also ship — Naive Bayes and an averaged perceptron over character n-grams (the same
shared-scoring design as `bifonia`). They score higher on sentence-length text
(~96% vs ~93% compatible accuracy, held-out 5-fold CV; see `benchmark/`):

```python
detect("o Antônio era um génio econômico", method="nb")          # learned
detect("o Antônio era um génio econômico", method="perceptron")  # learned
detect("o Antônio era um génio econômico")                       # rules (default)
```

The guard runs first in every mode, and rule markers are attached to a learned result
for explainability.

### Sister-language guard

Mirandese, Galician (especially reintegrationist), and Barranquenho look like
Portuguese but are not. `detect()` recognises and **flags** them rather than mangling
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
desacordo convert --from ao1990-pt --to ao1990-br --variant br "o facto"
desacordo norms          # list the available orthographic norms
```

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
several edges, **lexical and lossy** — dropping a silent consonant or an accent discards
information no rule can recover. `ConversionResult.lossless` / `.warnings` report this
instead of silently guessing.

## License

Apache-2.0.
