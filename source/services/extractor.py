import os
import json
import pdfplumber
import instructor
from litellm import completion
from pydantic import create_model, Field
from typing import Any, Optional
from datetime import datetime, date

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
        return float(s)
    except:
        return 0.0


def clean_date(val: Any) -> Optional[date]:
    """Konvertiert verschiedene Datumsformate in echte date-Objekte."""
    if not val: return None
    if isinstance(val, date): return val

    val_str = str(val).split('T')[0].strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except:
            continue
    return None


def get_dynamic_extraction_model(schema_data: dict, table_name: str):
    fields = {}
    columns = schema_data[table_name]["columns"]
    for col_name, col_type in columns.items():
        if col_name in ["id", "user_id", "file_data_id", "created_at", "updated_at"]:
            continue
        # KI extrahiert als String, wir konvertieren danach manuell
        fields[col_name] = (Optional[str], Field(None))
    return create_model(f"Dynamic{table_name.capitalize()}", **fields)


def extract_invoice_data(file_path: str, model_name: str = "ollama/gemma3:4b") -> dict:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, "db", "db_schema.json")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    schema_keys = {k.lower(): k for k in schema_data.keys()}
    actual_key = schema_keys.get("invoice")
    DynamicModel = get_dynamic_extraction_model(schema_data, actual_key)

    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = "\n".join([p.extract_text() for p in pdf.pages[:2] if p.extract_text()])

        # Aufruf OHNE 'mode=', da dieser bereits oben im 'client' definiert wurde
        extracted_obj = client.chat.completions.create(
            model=model_name,
            response_model=DynamicModel,
            messages=[
                {"role": "system",
                 "content": "Du bist ein präziser Daten-Extraktor. Extrahiere Beträge als Zahl und Daten als YYYY-MM-DD."},
                {"role": "user", "content": f"Text:\n{full_text}"}
            ]
        )

        raw_data = extracted_obj.model_dump()

        # --- MANUELLE NACHBEARBEITUNG FÜR SQLITE ---
        final_data = {}
        for k, v in raw_data.items():
            if "amount" in k:
                final_data[k] = clean_amount(v)
            elif "date" in k:
                final_data[k] = clean_date(v)
            else:
                final_data[k] = v

        return final_data

    except Exception as e:
        print(f"[Extraktions-Fehler] {e}")
        return None