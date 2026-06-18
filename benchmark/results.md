# desacordo_ortografico benchmark

Corpus: `gold_corpus.jsonl` — 1329 parallel sentences (6645 renderings across 5 norms).

## Conversion

| pair | exact-match | token-acc |
|------|-------------|-----------|
| etymological->pt_1973 | 1301/1329 = 97.9% | 99.8% |
| etymological->ao1990-pt | 1258/1329 = 94.7% | 99.4% |
| etymological->ao1990-br | 976/1329 = 73.4% | 96.1% |
| pt_1973->ao1990-pt | 1278/1329 = 96.2% | 99.6% |
| br_1971->ao1990-br | 1319/1329 = 99.2% | 99.9% |
| ao1990-pt->ao1990-br | 1187/1329 = 89.3% | 98.2% |
| ao1990-br->ao1990-pt | 1186/1329 = 89.2% | 98.2% |

**Overall: 91.4% exact-match, 98.7% token-accuracy over 9303 conversions.**

### Conversion accuracy by feature family

| feature | exact-match | n |
|---------|-------------|---|
| hyphen_rs | 69.9% | 385 |
| silent_pt | 83.1% | 378 |
| silent_ct | 85.4% | 2688 |
| divergence | 90.8% | 2058 |
| months | 91.0% | 357 |
| nasal | 91.4% | 3605 |
| ch_k | 92.4% | 567 |
| dual | 92.5% | 1358 |
| digraph | 94.1% | 2023 |
| differential | 94.3% | 511 |
| geminate | 95.0% | 1610 |
| diphthong | 96.9% | 1015 |
| trema | 97.4% | 819 |
| mn_ps | 99.1% | 336 |

## Detection

**Compatible accuracy: 96.1%** over 6645 renderings.

Confusion (nominal norm -> predicted, raw counts; off-diagonal often reflects norms that are spelling-identical for a given sentence):

| nominal \ predicted | ao1990 | ao1990-br | ao1990-pt | br_1971 | etymological | pt_1973 |
|---|---|---|---|---|---|---|
| etymological | 215 | 0 | 232 | 0 | 459 | 423 |
| pt_1973 | 478 | 0 | 325 | 1 | 2 | 523 |
| ao1990-pt | 821 | 1 | 505 | 2 | 0 | 0 |
| br_1971 | 555 | 419 | 4 | 224 | 0 | 127 |
| ao1990-br | 808 | 487 | 3 | 2 | 0 | 29 |

## Sister-language guard

**Accuracy: 93.3%** over 15 samples.

## Summary

- conversion exact-match: **91.4%**
- conversion token-accuracy: **98.7%**
- detection compatible accuracy: **96.1%**
- guard accuracy: **93.3%**
