# tools

## `scrape_portuguesaletra.py`

A small, stdlib-only client that scrapes the *Acordo Ortográfico* category of
[portuguesaletra.com](https://portuguesaletra.com/category/acordo-ortografico/) into a
dataset of words whose spelling the 1990 reform touched.

Each article documents one vocábulo with a fixed, labelled layout — pre-1990 European
(`Ortografia Antiga _1945`), pre-1990 Brazilian (`Ortografia Antiga _1943`), the AO1990
valid form(s) (`vocábulo(s) válido(s)`), and an `observações` note — which the client
parses into one JSON record per word.

```bash
python tools/scrape_portuguesaletra.py -o tools/portuguesaletra_ao.jsonl --delay 0.4
```

It walks the 263 category pages, then streams ~6.5k records to disk (flushed per row).
Polite by default: a real User-Agent, a delay between requests, retries with back-off, and
it honours the site's robots.txt (which only blocks `/cgi-bin` and named bad bots).

### Record schema

```json
{
  "slug": "protectorato-ou-protetorato-ao",
  "url":  "https://portuguesaletra.com/acordo-ortografico/protectorato-ou-protetorato-ao/",
  "title": "Protectorato ou Protetorato",
  "eu_1945": ["protectorato"],          // pre-1990 European form(s)
  "br_1943": ["protetorato"],           // pre-1990 Brazilian form(s)
  "ao1990":  ["protetorato"],           // AO1990 valid form(s)
  "notes":   "situação anterior é alterada!",
  "changed":    true,                   // from the observação note (true|false|null)
  "eu_changed": true,                   // European pre-1990 form not among the AO1990 forms
  "br_changed": false                   // Brazilian pre-1990 form not among the AO1990 forms
}
```

### Dataset (one run)

6,568 words; **2,897** have a changed European or Brazilian spelling, spanning every
AO1990 mechanism: silent c/p (`protectorato→protetorato`), open diphthong
(`mongolóide→mongoloide`), prefix hyphen → doubled r/s (`anti-sepsia→antissepsia`,
`ultra-sonoro→ultrassonoro`), and lexicalised hyphenation (`neo-romântica→neorromântica`).

The output `.jsonl` is git-ignored and regeneratable — it is third-party content
(portuguesaletra.com); check their terms before redistributing it.
