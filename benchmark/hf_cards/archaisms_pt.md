---
license: apache-2.0
language:
- pt
pretty_name: Portuguese pre-1911 spellings and their AO1990 forms
configs:
- config_name: default
  data_files: archaisms.csv
---

# Portuguese pre-1911 spellings

Each row gives a Portuguese word in the etymological spelling from before the reform of 1911. It also gives the spelling of the word under the Acordo Ortográfico de 1990 (AO1990). The file `archaisms.csv` has {rows} rows, one for each pre-1911 form of the table except `kermesse`. `kermesse` is the French spelling of the word. The reform of 1911 writes it `quermes` (Base I: "Escreveremos, pois, caleidoscópio, quermes").

## Columns

| Column | Content |
|---|---|
| `archaic` | The pre-1911 form, in lowercase (`pharmacia`). |
| `modern` | The AO1990 European Portuguese form (`farmácia`). |
| `modern_pt_BR` | The AO1990 Brazilian form where it is not the same as `modern` (`quilômetro`). Otherwise empty. |
| `notes` | The letter changes from `archaic` to `modern` (`ph→f + y→i`). |

## Sources

The rows come from the spelling table `data/spelling.json` of [desacordo_ortografico](https://github.com/TigreGotico/desacordo_ortografico). `modern` is the value of the AO1990 pt-PT row of the pre-1911 form in the table. `modern_pt_BR` is the value of its AO1990 pt-BR row, or the pt-PT value when the form has no pt-BR row. A pre-1911 form without an AO1990 row takes the forms that the function `convert()` of desacordo_ortografico gives it. Each row of the table cites its source. The pre-1911 rows cite these sources:

{sources}

`modern_pt_BR` follows the Vocabulário Ortográfico da Língua Portuguesa of the Academia Brasileira de Letras (VOLP) for the words in the VOLP data file of desacordo_ortografico. Where the VOLP lists two forms of one word, the column has the form with the consonant (`afecto`).
