# desacordo_ortografico benchmark

Corpus: `gold_corpus.jsonl` — 1341 parallel sentences (6705 renderings across 5 norms).

## Conversion

| pair | exact-match | token-acc |
|------|-------------|-----------|
| etymological->pt_1973 | 1057/1341 = 78.8% | 97.2% |
| etymological->ao1990-pt | 1126/1341 = 84.0% | 98.0% |
| etymological->ao1990-br | 730/1341 = 54.4% | 93.3% |
| pt_1973->ao1990-pt | 1234/1341 = 92.0% | 99.1% |
| br_1971->ao1990-br | 1322/1341 = 98.6% | 99.9% |
| ao1990-pt->ao1990-br | 1188/1341 = 88.6% | 98.1% |
| ao1990-br->ao1990-pt | 1192/1341 = 88.9% | 98.1% |

**Overall: 83.6% exact-match, 97.7% token-accuracy over 9387 conversions.**

### Conversion accuracy by feature family

| feature | exact-match | n |
|---------|-------------|---|
| hyphen_rs | 62.4% | 399 |
| silent_ct | 77.3% | 2709 |
| dual | 78.2% | 1358 |
| silent_pt | 80.5% | 364 |
| ch_k | 81.8% | 581 |
| trema | 82.1% | 840 |
| divergence | 84.6% | 2023 |
| nasal | 84.8% | 3661 |
| months | 85.7% | 350 |
| digraph | 86.2% | 2037 |
| differential | 87.7% | 616 |
| mn_ps | 89.9% | 336 |
| diphthong | 89.9% | 1001 |
| geminate | 90.0% | 1792 |

## Detection

**Compatible accuracy: 93.4%** over 6705 renderings.

Confusion (nominal norm -> predicted, raw counts; off-diagonal often reflects norms that are spelling-identical for a given sentence):

| nominal \ predicted | ao1990 | ao1990-br | ao1990-pt | br_1971 | etymological | not-portuguese | pt_1973 |
|---|---|---|---|---|---|---|---|
| etymological | 170 | 0 | 210 | 102 | 475 | 1 | 383 |
| pt_1973 | 509 | 0 | 330 | 1 | 2 | 1 | 498 |
| ao1990-pt | 833 | 1 | 503 | 2 | 0 | 1 | 1 |
| br_1971 | 555 | 418 | 6 | 228 | 0 | 1 | 133 |
| ao1990-br | 823 | 486 | 4 | 2 | 0 | 1 | 25 |

## Sister-language guard

**Accuracy: 93.3%** over 15 samples.

## Summary

- conversion exact-match: **83.6%**
- conversion token-accuracy: **97.7%**
- detection compatible accuracy: **93.4%**
- guard accuracy: **93.3%**
