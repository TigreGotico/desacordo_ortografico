"""AO1990 keeps European/Brazilian forms distinct where pronunciation differs."""
from desacordo_ortografico import OrthographyConverter

conv = OrthographyConverter()

print("== European AO1990 -> Brazilian AO1990 ==")
pt = "O facto do contacto foi húmido; o António ficou contente."
print(" ", pt)
print(" ", conv.convert(pt, "ao1990-pt", "ao1990-br").text)

print("\n== Every officially permitted spelling of a dual word ==")
for word in ["facto", "receção", "António", "casa"]:
    print(f"  {word:10} (PT) -> {conv.permitted_spellings(word, 'ao1990-pt')}")

print("\n== Dual-form alternatives surfaced during a conversion ==")
res = conv.convert("o facto e a receção", "ao1990-pt", "ao1990-br")
print("  text:", res.text)
for word, forms in res.alternatives.items():
    print(f"  alt: {word} -> {' | '.join(forms)}")
