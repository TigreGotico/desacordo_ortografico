# desacordo_ortografico benchmark

Corpus: `silver_corpus.jsonl` — 1329 parallel sentences (6645 renderings across 5 norms).

## Conversion

| pair | exact-match | token-acc |
|------|-------------|-----------|
| etymological->pt_1973 | 1321/1329 = 99.4% | 99.9% |
| etymological->ao1990-pt | 1302/1329 = 98.0% | 99.8% |
| etymological->ao1990-br | 1211/1329 = 91.1% | 98.4% |
| pt_1973->ao1990-pt | 1306/1329 = 98.3% | 99.8% |
| br_1971->ao1990-br | 1324/1329 = 99.6% | 100.0% |
| ao1990-pt->ao1990-br | 1208/1329 = 90.9% | 98.4% |
| ao1990-br->ao1990-pt | 1083/1329 = 81.5% | 97.3% |

**Overall: 94.1% exact-match, 99.1% token-accuracy over 9303 conversions.**

### Conversion accuracy by feature family

| feature | exact-match | n |
|---------|-------------|---|
| hyphen_rs | 82.1% | 385 |
| silent_pt | 83.3% | 378 |
| silent_ct | 91.7% | 2688 |
| divergence | 92.4% | 2058 |
| months | 93.6% | 357 |
| nasal | 94.0% | 3605 |
| dual | 94.0% | 1358 |
| differential | 95.9% | 511 |
| digraph | 96.0% | 2023 |
| geminate | 96.8% | 1610 |
| diphthong | 97.6% | 1015 |
| ch_k | 97.7% | 567 |
| trema | 98.2% | 819 |
| mn_ps | 100.0% | 336 |

## Detection

**Compatible accuracy: 92.6%** over 6645 renderings.

Confusion (nominal norm -> predicted, raw counts; off-diagonal often reflects norms that are spelling-identical for a given sentence):

| nominal \ predicted | ao1990 | ao1990-br | ao1990-pt | br_1971 | etymological | pt_1973 |
|---|---|---|---|---|---|---|
| etymological | 226 | 0 | 246 | 0 | 403 | 454 |
| pt_1973 | 462 | 0 | 319 | 0 | 1 | 547 |
| ao1990-pt | 804 | 1 | 524 | 0 | 0 | 0 |
| br_1971 | 555 | 397 | 15 | 224 | 0 | 138 |
| ao1990-br | 783 | 325 | 112 | 0 | 0 | 109 |

## Sister-language guard

**Accuracy: 93.3%** over 15 samples.

## Summary

- conversion exact-match: **94.1%**
- conversion token-accuracy: **99.1%**
- detection compatible accuracy: **92.6%**
- guard accuracy: **93.3%**
