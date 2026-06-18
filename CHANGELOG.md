# Changelog

## 0.0.1a1

Initial release.

- Detection of Portuguese orthography (era + national variant) from text, via an
  explainable rule scorer (default) or two shipped zero-dependency learned models —
  Naive Bayes and an averaged perceptron over character n-grams, selectable with
  `detect(text, method="nb"|"perceptron")` and `desacordo detect --method`.
- Conversion between any two norms on the historical graph: pre-1911 etymological,
  Reforma de 1911, Formulário 1943 (BR), Convenção 1945 (PT), the 1971/73 accent
  mini-reform, and AO1990 (European and Brazilian variants).
- Deterministic rule engine (Greek-digraph simplification, geminate reduction,
  nasal-vowel alternation, AO1990 accent/trema drops, prefix + r/s doubling,
  position-aware month casing, word-list-backed accent restoration and silent-c/p drop)
  plus curated, sourced exception lexicons (Base IV keep/drop/dual, differential accents,
  lexicalized hyphens, PT/BR divergences, ~200 pre-1911 etymological forms).
- AO1990 dual-form handling: variant-aware conversion and `permitted_spellings`.
- Sister-language guard flagging Mirandese, Galician, and Barranquenho.
- `desacordo` command-line interface.
- A parallel benchmark corpus (5 norms per sentence) and evaluation harness under
  `benchmark/`.
- AO1990 word data reused from `tugalex`.
