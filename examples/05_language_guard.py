"""The detector flags recognised sister varieties instead of mangling them."""
from desacordo_ortografico import detect
from desacordo_ortografico.guard import NotPortuguese

SAMPLES = [
    "A relaçom da naçom nom tem umha soluçom.",   # reintegrationist Galician
    "You falo la lhéngua mirandesa de l miu pais.",  # Mirandese
    "Oh irmõih ehtá na bê labá la roupa.",          # Barranquenho
    "O gato preto subiu ao telhado da casa.",       # genuine Portuguese
]

for text in SAMPLES:
    result = detect(text)
    if isinstance(result, NotPortuguese):
        print(f"[NOT PT] {result.name} (conf {result.confidence:.2f})  {text}")
        print(f"         {result.status}")
    else:
        print(f"[PT/{result.id}] (conf {result.confidence:.2f})  {text}")
