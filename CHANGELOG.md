# Changelog

## 0.0.1a1

Initial release.

- Detection of Portuguese orthography (era + national variant) from text.
- Conversion between any two norms on the historical graph: pre-1911 etymological,
  Reforma de 1911, Formulário 1943 (BR), Convenção 1945 (PT), the 1971/73 accent
  mini-reform, and AO1990 (European and Brazilian variants).
- Deterministic rule engine (Greek-digraph simplification, nasal-vowel alternation,
  AO1990 accent/trema drops, prefix + r/s doubling, month lowercasing) plus curated,
  sourced exception lexicons (Base IV keep/drop/dual, differential accents, lexicalized
  hyphens, PT/BR divergences, 1911 irregulars).
- AO1990 dual-form handling: variant-aware conversion and `permitted_spellings`.
- Sister-language guard flagging Mirandese, Galician, and Barranquenho.
- `desacordo` command-line interface.
- AO1990 word data reused from `tugalex`.
