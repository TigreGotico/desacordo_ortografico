# desacordo_ortografico benchmark

Corpus: `gold_corpus.jsonl` — 1341 parallel sentences (6705 renderings across 5 norms).

## Conversion

| pair | exact-match | token-acc |
|------|-------------|-----------|
| etymological->pt_1973 | 1136/1341 = 84.7% | 98.0% |
| etymological->ao1990-pt | 1131/1341 = 84.3% | 98.1% |
| etymological->ao1990-br | 891/1341 = 66.4% | 95.0% |
| pt_1973->ao1990-pt | 1234/1341 = 92.0% | 99.1% |
| br_1971->ao1990-br | 1322/1341 = 98.6% | 99.9% |
| ao1990-pt->ao1990-br | 1188/1341 = 88.6% | 98.1% |
| ao1990-br->ao1990-pt | 1192/1341 = 88.9% | 98.1% |

**Overall: 86.2% exact-match, 98.0% token-accuracy over 9387 conversions.**

### Conversion accuracy by feature family

| feature | exact-match | n |
|---------|-------------|---|
| hyphen_rs | 62.4% | 399 |
| silent_ct | 78.7% | 2709 |
| ch_k | 81.8% | 581 |
| silent_pt | 82.1% | 364 |
| digraph | 86.6% | 2037 |
| nasal | 86.8% | 3661 |
| divergence | 88.0% | 2023 |
| months | 89.1% | 350 |
| mn_ps | 90.2% | 336 |
| dual | 90.5% | 1358 |
| differential | 90.6% | 616 |
| geminate | 90.9% | 1792 |
| diphthong | 91.3% | 1001 |
| trema | 91.5% | 840 |

## Detection

**Compatible accuracy: 94.3%** over 6705 renderings.

Confusion (nominal norm -> predicted, raw counts; off-diagonal often reflects norms that are spelling-identical for a given sentence):

| nominal \ predicted | ao1990 | ao1990-br | ao1990-pt | br_1971 | etymological | not-portuguese | pt_1973 |
|---|---|---|---|---|---|---|---|
| etymological | 152 | 0 | 204 | 102 | 475 | 1 | 407 |
| pt_1973 | 480 | 0 | 323 | 1 | 2 | 1 | 534 |
| ao1990-pt | 833 | 1 | 503 | 2 | 0 | 1 | 1 |
| br_1971 | 554 | 418 | 6 | 228 | 0 | 1 | 134 |
| ao1990-br | 823 | 486 | 4 | 2 | 0 | 1 | 25 |

## Sister-language guard

**Accuracy: 93.3%** over 15 samples.

## Summary

- conversion exact-match: **86.2%**
- conversion token-accuracy: **98.0%**
- detection compatible accuracy: **94.3%**
- guard accuracy: **93.3%**
