# desacordo_ortografico benchmark

Corpus: `gold_corpus.jsonl` — 1316 parallel sentences (6580 renderings across 5 norms).

## Conversion

| pair | exact-match | token-acc |
|------|-------------|-----------|
| etymological->pt_1973 | 1129/1316 = 85.8% | 98.3% |
| etymological->ao1990-pt | 1178/1316 = 89.5% | 98.8% |
| etymological->ao1990-br | 893/1316 = 67.9% | 95.2% |
| pt_1973->ao1990-pt | 1266/1316 = 96.2% | 99.6% |
| br_1971->ao1990-br | 1307/1316 = 99.3% | 99.9% |
| ao1990-pt->ao1990-br | 1174/1316 = 89.2% | 98.2% |
| ao1990-br->ao1990-pt | 1173/1316 = 89.1% | 98.2% |

**Overall: 88.1% exact-match, 98.3% token-accuracy over 9212 conversions.**

### Conversion accuracy by feature family

| feature | exact-match | n |
|---------|-------------|---|
| hyphen_rs | 63.5% | 378 |
| silent_ct | 82.4% | 2681 |
| ch_k | 83.4% | 560 |
| silent_pt | 86.6% | 350 |
| nasal | 88.3% | 3605 |
| digraph | 89.0% | 1967 |
| months | 89.1% | 350 |
| divergence | 89.5% | 2002 |
| mn_ps | 90.9% | 329 |
| dual | 91.6% | 1351 |
| diphthong | 92.1% | 994 |
| geminate | 92.7% | 1785 |
| differential | 94.0% | 581 |
| trema | 94.4% | 805 |

## Detection

**Compatible accuracy: 94.4%** over 6580 renderings.

Confusion (nominal norm -> predicted, raw counts; off-diagonal often reflects norms that are spelling-identical for a given sentence):

| nominal \ predicted | ao1990 | ao1990-br | ao1990-pt | br_1971 | etymological | pt_1973 |
|---|---|---|---|---|---|---|
| etymological | 150 | 0 | 204 | 101 | 463 | 398 |
| pt_1973 | 472 | 0 | 319 | 1 | 2 | 522 |
| ao1990-pt | 814 | 1 | 499 | 2 | 0 | 0 |
| br_1971 | 543 | 414 | 6 | 223 | 0 | 130 |
| ao1990-br | 801 | 481 | 3 | 2 | 0 | 29 |

## Sister-language guard

**Accuracy: 93.3%** over 15 samples.

## Summary

- conversion exact-match: **88.1%**
- conversion token-accuracy: **98.3%**
- detection compatible accuracy: **94.4%**
- guard accuracy: **93.3%**
