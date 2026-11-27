# desacordo_ortografico

<!-- agent-hint
covers: what the package does, how to install it and the first detect and convert calls
source: `desacordo_ortografico/__init__.py`, `desacordo_ortografico/convert.py:convert`, `desacordo_ortografico/detect.py:detect`
generated: no
verify: d=$(mktemp -d) && sed '/^```/d' README.md > $d/r.txt && python -I -m doctest $d/r.txt
see: `docs/index.md`, `docs/quickstart.md`, `AGENTS.md`
-->

`desacordo_ortografico` converts Portuguese text between spelling norms: the pre-1911 etymological writing, the Reforma de 1911, the Brazilian norms of 1943 and 1971, the European norms of 1945 and 1973, and the Acordo Ortográfico de 1990 (AO1990) in its European and Brazilian forms. It also detects which norm a text follows, and it flags Mirandese, Galician and Barranquenho text instead of converting it.

## Install

```bash
pip install desacordo_ortografico
```

## Quick start

```python
>>> from desacordo_ortografico import detect, convert
>>> detect("a pharmacia do theatro").id
'etymological'
>>> detect("o facto é óptimo").id
'pt_1973'
>>> convert("pharmacia", "etymological", "ao1990-br")
'farmácia'
>>> convert("a acção directa", "pre-ao1990-pt", "ao1990-pt")
'a ação direta'
```

The command line does the same:

```bash
desacordo convert --from pre-ao1990-pt --to ao1990-pt "a acção directa"
```

## Documentation

The documentation starts at [docs/index.md](docs/index.md).

| Page | You get |
|---|---|
| [docs/quickstart.md](docs/quickstart.md) | Install, detection, conversion, the command line and the full result object, with real output |
| [docs/api.md](docs/api.md) | Every public name, its signature and its default |
| [docs/features.md](docs/features.md) | The 28 conversion features and what each one changes |
| [docs/orthographies.md](docs/orthographies.md) | The eight norms, their graph and the official source of each rule |
| [docs/data.md](docs/data.md) | The JSON data files and the Hugging Face datasets |

## License

Apache-2.0.
