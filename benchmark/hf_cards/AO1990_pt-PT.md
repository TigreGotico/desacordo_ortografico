---
license: apache-2.0
language:
- pt
pretty_name: AO1990 spelling changes in European Portuguese
configs:
- config_name: default
  data_files: acordo_ortografico_pt_PT.csv
---

# AO1990 spelling changes in European Portuguese

Each row gives a European Portuguese word in the spelling from before the Acordo Ortográfico de 1990 (AO1990), and its AO1990 spelling. The file `acordo_ortografico_pt_PT.csv` has {rows} rows. A row with two or more old spellings gives the AO1990 spelling of each of them.

## Columns

| Column | Content |
|---|---|
| `old_form` | The spelling of the Acordo Ortográfico of 1945 with the changes of 1973 (`acção`). |
| `new_form` | The AO1990 spelling (`ação`). Where the AO1990 permits two spellings, the cell has the two, in source order, with a comma and a space between them (`accipitrino, acipitrino`). |

## Sources

The rows come from the spelling table `data/spelling.json` of [desacordo_ortografico](https://github.com/TigreGotico/desacordo_ortografico). Each row of the table cites its source. The rows of this dataset cite these sources:

{sources}
