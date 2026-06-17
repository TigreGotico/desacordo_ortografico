"""Detect which Portuguese orthography a text is written in."""
from desacordo_ortografico import detect

SAMPLES = [
    "A pharmacia do theatro tinha um lyrio.",   # pre-1911 etymological
    "O facto é que estava óptimo e correcto.",  # pre-AO1990, European
    "A idéia do vôo deu-lhe uma sensação boa.",  # pre-AO1990, Brazilian
    "A ação direta foi ótima e objetiva.",       # AO1990
    "O António é económico e fenomenal.",        # AO1990, European variant
    "O Antônio é econômico e fenomenal.",        # AO1990, Brazilian variant
]

for text in SAMPLES:
    result = detect(text)
    print(f"{result.id:18} (conf {result.confidence:.2f})  {text}")
    if result.note:
        print(f"{'':18} -> {result.note}")
