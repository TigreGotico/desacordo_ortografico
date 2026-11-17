---
license: apache-2.0
language:
- pt
pretty_name: AO1990 spelling changes in Brazilian Portuguese
configs:
- config_name: default
  data_files: acordo_ortografico_pt_BR.csv
---

# AO1990 spelling changes in Brazilian Portuguese

Each row gives a Brazilian Portuguese word in the spelling from before the Acordo Ortográfico de 1990 (AO1990), and its AO1990 spelling. The file `acordo_ortografico_pt_BR.csv` has {rows} rows. A row with two or more old spellings gives the AO1990 spelling of each of them.

## Columns

| Column | Content |
|---|---|
| `old_form` | A spelling from before the AO1990, mostly the spelling of the Formulário Ortográfico of 1943 with the changes of Lei 5.765/1971 (`idéia`). Some rows give a 1943 spelling that Lei 5.765/1971 removed (`pôlo`). |
| `new_form` | The AO1990 spelling (`ideia`). Where the AO1990 permits two spellings, the cell has the two, in source order, with a comma and a space between them (`codialeto, codialecto`). |

## Sources

The rows come from the spelling table `data/spelling.json` of [desacordo_ortografico](https://github.com/TigreGotico/desacordo_ortografico). Each row of the table cites its source. The rows of this dataset cite these sources:

{sources}
