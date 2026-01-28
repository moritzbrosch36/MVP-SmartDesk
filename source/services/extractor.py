import os
import json
import time
import pdfplumber
import instructor
from litellm import completion
from pydantic import create_model, Field
from typing import Any, Optional
from datetime import datetime, date
from source.utils.logger import get_pdf_logger, get_llm_logger

# Logger initialisieren
pdf_logger = get_pdf_logger()
llm_logger = get_llm_logger()

# --- WICHTIG: Mode hier beim Client-Patch festlegen für maximale Stabilität ---
client = instructor.from_litellm(completion, mode=instructor.Mode.JSON)


def clean_amount(val: Any) -> float:
    """Bereinigt deutsche Beträge und achtet auf Cent-Stellen."""
    if val is None or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)

    s = str(val).strip()

    # Wenn ein Komma vorkommt (typisch Deutsch: 1.200,50)
    if ',' in s:
        # Alles außer Komma und Ziffern entfernen (Tausenderpunkte weg)
        s = s.replace('.', '')
        # Komma durch Punkt ersetzen für Python float
        s = s.replace(',', '.')

    # Nur Ziffern und den Punkt behalten
    s = ''.join(c for c in s if c.isdigit() or c == '.')

    try:
        result = float(s)
        pdf_logger.debug(f"Betrag bereinigt: '{val}' → {result}")
        return result
    except Exception as e:
        pdf_logger.warning(f"Betrag konnte nicht konvertiert werden: '{val}' - {e}")
        return 0.0


def clean_date(val: Any) -> Optional[date]:
    """Konvertiert verschiedene Datumsformate in echte date-Objekte."""
    if not val: return None
    if isinstance(val, date): return val

    val_str = str(val).split('T')[0].strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            result = datetime.strptime(val_str, fmt).date()
            pdf_logger.debug(f"Datum konvertiert: '{val}' → {result} (Format: {fmt})")
            return result
        except:
            continue

    pdf_logger.warning(f"Datum konnte nicht konvertiert werden: '{val}'")
    return None


def get_dynamic_extraction_model(schema_data: dict, table_name: str):
    """Erstellt dynamisches Pydantic-Modell basierend auf Schema."""
    fields = {}
    columns = schema_data[table_name]["columns"]
    excluded_fields = ["id", "user_id", "file_data_id", "created_at", "updated_at"]

    for col_name, col_type in columns.items():
        if col_name in excluded_fields:
            continue
        # KI extrahiert als String, wir konvertieren danach manuell
        fields[col_name] = (Optional[str], Field(None))

    pdf_logger.debug(f"Dynamisches Modell erstellt für '{table_name}' mit {len(fields)} Feldern")
    return create_model(f"Dynamic{table_name.capitalize()}", **fields)


def extract_invoice_data(file_path: str, model_name: str = "ollama/gemma3:4b") -> dict:
    """
    Extrahiert Rechnungsdaten aus PDF mit LLM.

    Args:
        file_path: Pfad zur PDF-Datei
        model_name: LLM-Modell für Extraktion

    Returns:
        Dictionary mit extrahierten Daten oder None bei Fehler
    """
    filename = os.path.basename(file_path)
    pdf_logger.info(f"Starte Datenextraktion: {filename}")
    start_time = time.time()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, "db", "db_schema.json")

    try:
        # Schema laden
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_data = json.load(f)

        schema_keys = {k.lower(): k for k in schema_data.keys()}
        actual_key = schema_keys.get("invoice")

        if not actual_key:
            pdf_logger.error("Tabelle 'invoice' nicht im Schema gefunden")
            return None

        DynamicModel = get_dynamic_extraction_model(schema_data, actual_key)

        # PDF Text extrahieren
        pdf_start = time.time()
        with pdfplumber.open(file_path) as pdf:
            full_text = "\n".join([p.extract_text() for p in pdf.pages[:2] if p.extract_text()])

        pdf_time = time.time() - pdf_start
        pdf_logger.info(f"PDF-Text extrahiert: {filename} | {len(full_text)} Zeichen | {pdf_time:.2f}s")

        if not full_text or len(full_text) < 50:
            pdf_logger.warning(f"Zu wenig Text extrahiert aus {filename} ({len(full_text)} Zeichen)")
            return None

        # LLM Extraktion
        llm_logger.info(f"Starte LLM-Extraktion für: {filename}")
        llm_start = time.time()

        extracted_obj = client.chat.completions.create(
            model=model_name,
            response_model=DynamicModel,
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein präziser Daten-Extraktor. "
                               "Extrahiere Beträge als Zahl und Daten als YYYY-MM-DD."
                },
                {
                    "role": "user",
                    "content": f"Text:\n{full_text}"
                }
            ]
        )

        llm_time = time.time() - llm_start
        raw_data = extracted_obj.model_dump()
        llm_logger.info(
            f"LLM-Extraktion erfolgreich: {filename} | "
            f"Zeit: {llm_time:.2f}s | "
            f"Felder extrahiert: {len([v for v in raw_data.values() if v])}"
        )
        llm_logger.debug(f"Rohdaten: {raw_data}")

        # --- MANUELLE NACHBEARBEITUNG FÜR SQLITE ---
        final_data = {}
        for k, v in raw_data.items():
            if "amount" in k:
                final_data[k] = clean_amount(v)
            elif "date" in k:
                final_data[k] = clean_date(v)
            else:
                final_data[k] = v

        total_time = time.time() - start_time
        pdf_logger.info(
            f"Extraktion abgeschlossen: {filename} | "
            f"Gesamtzeit: {total_time:.2f}s | "
            f"Erfolgreich extrahierte Felder: {len([v for v in final_data.values() if v])}"
        )
        pdf_logger.debug(f"Finale Daten: {final_data}")

        return final_data

    except FileNotFoundError as e:
        pdf_logger.error(f"Datei nicht gefunden: {file_path}", exc_info=True)
        return None
    except json.JSONDecodeError as e:
        pdf_logger.error(f"Schema-Datei konnte nicht gelesen werden: {schema_path}", exc_info=True)
        return None
    except Exception as e:
        total_time = time.time() - start_time
        pdf_logger.error(
            f"Extraktion fehlgeschlagen: {filename} | "
            f"Zeit: {total_time:.2f}s | "
            f"Fehler: {e}",
            exc_info=True
        )
        return None
