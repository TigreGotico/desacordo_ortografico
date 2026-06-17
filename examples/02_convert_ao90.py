"""Convert between the pre-AO1990 norms and AO1990."""
from desacordo_ortografico import OrthographyConverter

conv = OrthographyConverter()

print("== pre-AO1990 European -> AO1990 (PT) ==")
pt_old = "A acção do director era óptima e correcta."
print(" ", pt_old)
print(" ", conv.convert(pt_old, "pre-ao1990-pt", "ao1990-pt").text)

print("\n== pre-AO1990 Brazilian -> AO1990 (BR) ==")
br_old = "A idéia do vôo e da freqüência era ótima."
print(" ", br_old)
print(" ", conv.convert(br_old, "pre-ao1990-br", "ao1990-br").text)

print("\n== AO1990 -> pre-AO1990 (reverse is lexical / lossy) ==")
res = conv.convert("A ação do diretor era ótima.", "ao1990-pt", "pre-ao1990-pt")
print(" ", res.text)
print("  lossless:", res.lossless)
for w in res.warnings:
    print("  warning:", w)
