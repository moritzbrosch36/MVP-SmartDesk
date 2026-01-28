import json
import os
import pdfplumber
import instructor
from litellm import completion
from pydantic import BaseModel, Field


# 1. Kleines Modell für die Ja/Nein Entscheidung
class ClassificationResult(BaseModel):
    is_invoice: bool = Field(description="Ist das Dokument eine Rechnung oder ein Beleg?")
    confidence: float = Field(description="Sicherheit der Entscheidung zwischen 0 und 1")


# Instructor Client initialisieren
client = instructor.from_litellm(completion)


def is_invoice(file_path: str) -> bool:
    """Hybride Prüfung: Keywords (schnell) + KI via Instructor (präzise)."""

    # Pfad zur rules.json dynamisch ermitteln
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "rules.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            rules = json.load(f)

        with pdfplumber.open(file_path) as pdf:
            text_sample = pdf.pages[0].extract_text()
            if not text_sample:
                return False

            text_lower = text_sample.lower()

            # --- STUFE 1: Keyword-Check (Schnellfilter) ---
            has_indicator = any(word in text_lower for word in rules["invoice_indicators"])
            is_excluded = any(word in text_lower for word in rules["exclusion_keywords"])

            # Wenn keine Keywords da sind, ist es sehr wahrscheinlich keine Rechnung
            if not has_indicator or is_excluded:
                return False

            # --- STUFE 2: KI-Validierung via Instructor ---
            # Nur wenn Stufe 1 bestanden wurde, fragen wir Gemma 3
            return _ai_validation(text_sample[:1500])

    except Exception as e:
        print(f"Fehler bei Klassifizierung von {file_path}: {e}")
        return False


def _ai_validation(text_snippet: str) -> bool:
    """Nutzt Instructor, um eine saubere boolesche Antwort zu erhalten."""
    try:
        response = client.chat.completions.create(
            model="ollama/gemma3:4b",
            response_model=ClassificationResult,
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein Dokumenten-Klassifizierer. Entscheide, ob der Text zu einer RECHNUNG oder einem BELEG gehört."
                },
                {"role": "user", "content": f"Dokumentenausschnitt:\n{text_snippet}"}
            ]
        )
        return response.is_invoice
    except Exception as e:
        print(f"[KI-Klassifizierung Fehler] {e}")
        # Im Zweifel False, um die Datenbank sauber zu halten
        return False