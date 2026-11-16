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

Each row gives a Portuguese word in the etymological spelling from before the reform of 1911. It also gives the spelling of the word under the Acordo Ortográfico de 1990 (AO1990). The file `archaisms.csv` has {rows} rows, one for each pre-1911 form.

## Columns

| Column | Content |
|---|---|
| `archaic` | The pre-1911 form, in lowercase (`pharmacia`). |
| `modern` | The AO1990 European Portuguese form (`farmácia`). |
| `modern_pt_BR` | The AO1990 Brazilian form where it is not the same as `modern` (`quilômetro`). Otherwise empty. |
| `notes` | The letter changes from `archaic` to `modern` (`ph→f`), where the source list gives them. Otherwise empty. |

## Sources

The rows come from the spelling table `data/spelling.json` of [desacordo_ortografico](https://github.com/TigreGotico/desacordo_ortografico). `modern` and `modern_pt_BR` are the AO1990 forms that desacordo_ortografico gives each pre-1911 form. Each row of the table cites its source. The pre-1911 rows cite these sources:

{sources}

`modern_pt_BR` follows the Vocabulário Ortográfico da Língua Portuguesa of the Academia Brasileira de Letras (VOLP) for the words that it lists. Where the VOLP lists two forms of one word, the column has the form with the consonant (`afecto`).
