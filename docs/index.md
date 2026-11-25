# desacordo_ortografico documentation

<!-- agent-hint
covers: every documentation page in reading order, with what the reader gets from each
source: `docs/`
generated: no
verify: diff <(ls docs/*.md | xargs -n1 basename | grep -v '^index.md$' | LC_ALL=C sort) <(grep -o '^| \[[^]]*\]([a-z_]*\.md)' docs/index.md | sed 's/.*(\(.*\))/\1/' | LC_ALL=C sort)
see: `../README.md`, `../AGENTS.md`
-->

`desacordo_ortografico` detects and converts Portuguese spelling norms. These pages show how to use it and what each rule rests on.

| Page | You get |
|---|---|
| [quickstart.md](quickstart.md) | Install, then detect, convert and read the full result with its warnings, with real output |
| [api.md](api.md) | Every public name with its signature and default, the detection confidence table and the known limits |
| [features.md](features.md) | The 28 conversion features by edge, a chart of the words each one changes, and the rules of the word maps and the 1911 accent guess |
| [orthographies.md](orthographies.md) | The eight norms, the rules that separate them and the official source of each rule |
| [data.md](data.md) | Each JSON data file, how rows cite their source, and the Hugging Face datasets |

## Pick a starting page

| You want to | Start with |
|---|---|
| Convert or detect text | [quickstart.md](quickstart.md) |
| Look up a function or a default | [api.md](api.md) |
| Turn one conversion feature on or off, or see what it does | [features.md](features.md) |
| Know why a form converts the way it does | [orthographies.md](orthographies.md) |
| Add or correct a word row | [data.md](data.md) |
| Change the repository | [AGENTS.md](../AGENTS.md) |

The [benchmark README](../benchmark/README.md) describes the silver corpus and the scoring scripts. The [tools README](../tools/README.md) describes the data-building and chart scripts.

---
[Home](../README.md) · [Quickstart →](quickstart.md)
