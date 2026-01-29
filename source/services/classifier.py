import json
import os
import time
import pdfplumber
import instructor
from litellm import completion
from pydantic import BaseModel, Field
from source.utils.logger import get_classifier_logger, get_llm_logger

# Logger initialisieren
classifier_logger = get_classifier_logger()
llm_logger = get_llm_logger()


class ClassificationResult(BaseModel):
    is_invoice: bool = Field(description="Ist das Dokument eine Rechnung oder ein Beleg?")
    confidence: float = Field(description="Sicherheit der Entscheidung zwischen 0 und 1")


client = instructor.from_litellm(completion)


def is_invoice(file_path: str) -> bool:
    """Hybride Prüfung: Keywords (schnell) + KI via Instructor (präzise)."""

    classifier_logger.info(f"Starte Klassifizierung: {os.path.basename(file_path)}")
    start_time = time.time()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "rules.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            rules = json.load(f)

        # PDF Extraktion
        pdf_start = time.time()
        with pdfplumber.open(file_path) as pdf:
            text_sample = pdf.pages[0].extract_text()
            if not text_sample:
                classifier_logger.warning(f"Kein Text extrahiert: {os.path.basename(file_path)}")
                return False

            pdf_time = time.time() - pdf_start
            classifier_logger.debug(f"PDF-Extraktion: {pdf_time:.2f}s, {len(text_sample)} Zeichen")

            text_lower = text_sample.lower()

            # Keyword Check
            keyword_start = time.time()
            has_indicator = any(word in text_lower for word in rules["invoice_indicators"])
            is_excluded = any(word in text_lower for word in rules["exclusion_keywords"])
            keyword_time = time.time() - keyword_start

            classifier_logger.debug(
                f"Keyword-Check: {keyword_time:.3f}s | "
                f"Indicators: {has_indicator} | Excluded: {is_excluded}"
            )

            if not has_indicator or is_excluded:
                total_time = time.time() - start_time
                classifier_logger.info(
                    f"Keine Rechnung (Keyword-Filter): {os.path.basename(file_path)} "
                    f"[{total_time:.2f}s]"
                )
                return False

            # AI Validierung
            result = _ai_validation(text_sample[:1500], os.path.basename(file_path))

            total_time = time.time() - start_time
            classifier_logger.info(
                f"Klassifizierung abgeschlossen: {os.path.basename(file_path)} | "
                f"Ergebnis: {result} | Zeit: {total_time:.2f}s"
            )

            return result

    except Exception as e:
        classifier_logger.error(
            f"Fehler bei Klassifizierung von {os.path.basename(file_path)}: {e}",
            exc_info=True
        )
        return False


def _ai_validation(text_snippet: str, filename: str) -> bool:
    """Nutzt Instructor, um eine saubere boolesche Antwort zu erhalten."""

    llm_logger.info(f"Starte AI-Validierung für: {filename}")
    start_time = time.time()

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

        duration = time.time() - start_time
        llm_logger.info(
            f"AI-Validierung erfolgreich: {filename} | "
            f"Ergebnis: {response.is_invoice} | "
            f"Confidence: {response.confidence:.2f} | "
            f"Zeit: {duration:.2f}s"
        )

        return response.is_invoice

    except Exception as e:
        llm_logger.error(
            f"AI-Validierung fehlgeschlagen für {filename}: {e}",
            exc_info=True
        )
        return False