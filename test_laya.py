
import json
from laya import Router

# Carga el checkpoint multilingüe en la primera ejecución
router = Router()

texto = """
Carlos entró en la habitación y encontró a Laura.

—¿Dónde estabas? —preguntó Laura.

—¡No es asunto tuyo! —gritó Carlos furioso.

—Por favor, no grites —susurró ella.
"""

questions = {
    "tipo": {
        "type": "choice",
        "instructions": "Clasifica el fragmento de Carlos: ¡No es asunto tuyo!",
        "criteria": {
            "dialogo": "Palabras pronunciadas por un personaje",
            "narracion": "Descripción narrativa de hechos",
            "pensamiento": "Pensamiento interno de un personaje"
        }
    },
    "hablante": {
        "type": "choice",
        "instructions": "¿Quién pronuncia ¡No es asunto tuyo!?",
        "criteria": {
            "carlos": "Carlos pronuncia la frase",
            "laura": "Laura pronuncia la frase",
            "desconocido": "No es posible identificar al hablante"
        }
    },
    "emocion": {
        "type": "choice",
        "instructions": "¿Qué emoción expresa Carlos al decir ¡No es asunto tuyo!?",
        "criteria": {
            "enfado": "Ira, furia o enfado",
            "miedo": "Temor o inseguridad",
            "tristeza": "Pena o tristeza",
            "neutral": "No hay una emoción claramente expresada"
        }
    },
    "estilo": {
        "type": "choice",
        "instructions": "¿Cómo pronuncia Carlos la frase?",
        "criteria": {
            "grito": "Grita o eleva mucho la voz",
            "susurro": "Susurra o habla en voz muy baja",
            "normal": "Habla con volumen normal"
        }
    }
}

result = router.predict(
    texto,
    questions,
    model="multilingual"
)

print(json.dumps(result, ensure_ascii=False, indent=2))
