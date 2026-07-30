# The Portuguese orthographies

A reference for the norms this library models, the rules that separate them, and the
official sources. The central fact: Portuguese orthography is a **(variant × era)
matrix**. From 1911 to the late 2000s two official standards ran in parallel: a
European/PALOP line and a Brazilian line. AO1990 still permits divergent forms.

```
European / PALOP:  etymological → 1911 → 1945 → 1973 → AO1990 (PT)
Brazilian:         etymological → 1911 → 1943 → 1971 → AO1990 (BR)
```

Each transform is flagged **deterministic** (a clean, reversible regex) or **lexical**
(needs an exception list, usually one-way).

## Pre-1911: etymological / pseudo-etymological

No official norm existed. Spelling displayed real or imagined Greek/Latin ancestry.
Hallmarks: Greek digraphs `ph, th, rh, ch`(=/k/), `y`, geminates `ll, nn, mm, pp, tt`,
etymological silent consonants, and medial `h`. Detection is fairly deterministic
because the digraphs are characteristic. Generating pre-1911 spellings is lexical.

`pharmacia→farmácia · theatro→teatro · elle→ele · anno→ano · lyrio→lírio · sciencia→ciência`

## Reforma Ortográfica de 1911 (Portugal)

First official orthography (Portaria of 1 Sept 1911, commission of Gonçalves Viana).
It applied to Portugal and its colonies. **Brazil did not take part**, and this split
the two orthographies.

| rule | type |
|------|------|
| `ph→f`, `th→t`, `rh→r`, `y→i` | deterministic |
| `ch`(=/k/)→`c`/`qu`, geminate reduction (keep `rr`, `ss`), drop silent consonants and medial `h` | lexical |

Sources: [Reforma Ortográfica de 1911](https://pt.wikipedia.org/wiki/Reforma_Ortogr%C3%A1fica_de_1911) ·
[A ortografia antes de 1911 (Ciberdúvidas)](https://ciberduvidas.iscte-iul.pt/consultorio/perguntas/a-ortografia-antes-de-1911/33429)

## Formulário Ortográfico de 1943 (Brazil)

ABL, 12 Aug 1943. This was Brazil's governing norm (with the 1971 amendments) until
AO1990. Defining traits versus the European line: Brazil **dropped the silent c/p**
(`ação`, `ótimo`, `diretor`) and used the **acute** on stressed open vowels before a
nasal where Portugal used the circumflex/closed vowel (`Antônio`, `gênero`).

Source: [Formulário Ortográfico (Academia Brasileira de Letras)](https://www.academia.org.br/nossa-lingua/formulario-ortografico)

## Convenção Ortográfica Luso-Brasileira de 1945 (Portugal + PALOP)

ACL + ABL, 6 Oct 1945, Decreto 35.228. It was in force in Portugal and all PALOP until
AO1990. **Brazil signed but never ratified it**, keeping the 1943 Formulário instead.
This froze the two-standard system. It codified the PT/BR differences:

| phenomenon | PT-1945 | BR-1943 | type |
|---|---|---|---|
| silent c/p | `acção, óptimo, director` | `ação, ótimo, diretor` | lexical |
| open vowel before nasal | `António, fenómeno, génio` | `Antônio, fenômeno, gênio` | **deterministic** (é/ó ↔ ê/ô) |
| pronunciation divergences | `facto, húmido` | `fato, úmido` | lexical |

Source (official text): [Convenção Ortográfica de 1945 (Priberam)](https://www.priberam.pt/docs/AcOrtog45_73.pdf)

## Mini-reform of 1971 (BR) / 1973 (PT)

Lei 5.765/1971 (Brazil) and Decreto-Lei 32/73 (Portugal). This reform is accent-only
and mostly deterministic. The base PT/BR differences are untouched.

- Abolition of the **differential circumflex** on a closed homograph list
  (`êle→ele, govêrno→governo, sêca→seca`): deterministic (list).
- Abolition of the **grave/circumflex on subtonic syllables** of derived words
  (`sòmente→somente, cafèzinho→cafezinho`): deterministic (strip the grave accent).

Source: [Convenção Ortográfica de 1945 / 1973 accent reform (Priberam)](https://www.priberam.pt/docs/AcOrtog45_73.pdf)

## Acordo Ortográfico de 1990

Signed 16 Dec 1990 by the seven (then eight, with Timor-Leste) CPLP states. It took
force from 2006 (2nd Protocol), and became mandatory in Brazil in 2016 and Portugal
in 2015.

**Base IV, consonant sequences `cc, cç, ct, pc, pç, pt`**, is the hardest, irreducibly
lexical part. It defines three sets:
- **keep** (pronounced everywhere): `pacto, ficção, apto, egípcio, rapto`.
- **drop** (mute everywhere): `acção→ação, óptimo→ótimo, director→diretor`.
- **dual** (pronounced in one norm only, one spelling per norm):
  `facto`(PT)/`fato`(BR), `receção`(PT)/`recepção`(BR), `aspeto`(PT)/`aspecto`(BR).

**Accentuation** is mostly deterministic:
- Drop the acute on open `éi/ói` in **paroxytones**: `idéia→ideia, heróico→heroico`
  (oxytones keep theirs: `herói, papéis`).
- Drop the circumflex on `ôo` and `-êem`: `vôo→voo, lêem→leem`.
- Drop differential accents (closed list): `pára→para, pêlo→pelo, pólo→polo, pêra→pera`
  (kept: `pôr, pôde, têm, vêm`).

**Trema** is abolished (`freqüência→frequência`): deterministic, with a Brazil-only
effect. **Months and seasons** are lowercased: deterministic (closed list).
**Hyphenation**: a prefix-vowel plus `r/s` drops the hyphen and doubles the consonant
(`anti-religioso→antirreligioso`), which is deterministic. Lexicalized compounds
(`pára-quedas→paraquedas`) are lexical.

**AO1990 is two targets.** It sanctions divergent PT/BR forms (Base IV §1c and the
nasal-vowel alternation), so the library models `ao1990-pt` and `ao1990-br` separately.

Sources: [Base IV, das sequências consonânticas (FLiP)](https://www.flip.pt/Acordo-Ortografico/Texto/Base-IV-Das-sequencias-consonanticas/) ·
[Nota explicativa do AO90 (Academia das Ciências de Lisboa)](https://vocabulario.acad-ciencias.pt/index.php/ortografia/nota-explicativa-do-ao90) ·
[Acordo Ortográfico de 1990, texto oficial (Priberam)](https://www.priberam.pt/docs/AcOrtog90.pdf)

## Sister varieties (detected, never converted)

These are recognized in the Iberian/Lusophone space but are **not** Portuguese
orthographies. The library flags them (`NotPortuguese`) instead of mangling them.

- **Mirandese** (`mwl`) — an Astur-Leonese language, co-official in the Terra de
  Miranda (Lei 7/99). Markers: word-initial `lh-`, the article `l/ls`, `you`, `bós`.
- **Galician** (`gl`) — the closest relative of Portuguese. The standard (RAG/ILG)
  uses `ñ, ll`, and the reintegrationist standard uses near-Portuguese spelling
  (`-çom, nom, umha`).
- **Barranquenho** — a Portuguese-Spanish contact variety of Barrancos, recognized and
  protected as intangible cultural heritage by **Lei 97/2021** (not co-official). Its
  orthography (Univ. de Évora and CM Barrancos, June 2025) is a **draft in public
  consultation**, not a legally adopted norm, so it is flag-only. Markers: the
  aspiration grapheme `h` (`maih, ehtá`), betacism (`bê, labá`), and dropped
  infinitive `-r`.

Sources: [Lei 97/2021 (Diário da República)](https://files.dre.pt/1s/2021/12/25200/0000300004.pdf) ·
Lei 7/99 · [Língua mirandesa (Wikipedia)](https://pt.wikipedia.org/wiki/L%C3%ADngua_mirandesa) ·
[Reintegrationism (Wikipedia)](https://en.wikipedia.org/wiki/Reintegrationism)

---
[← API reference](api.md) · [Home](../README.md)
