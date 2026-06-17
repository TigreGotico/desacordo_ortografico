"""Walk a word across the whole timeline, from etymological spelling to AO1990."""
from desacordo_ortografico import OrthographyConverter

conv = OrthographyConverter()

chain = ["etymological", "reforma_1911", "pt_1945", "pt_1973", "ao1990-pt"]
text = "A pharmacia tinha orthographia antiga."

print("Forward through the European line:")
current = text
print(f"  {'(start)':14} {current}")
for nxt in chain[1:]:
    current = conv.convert(text, "etymological", nxt).text
    print(f"  {nxt:14} {current}")

print("\nSingle hop, etymological -> AO1990 (Brazilian):")
print(" ", conv.convert(text, "etymological", "ao1990-br").text)
