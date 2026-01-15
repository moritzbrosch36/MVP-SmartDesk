import json
from pathlib import Path
import instructor
from litellm import completion
from pydantic import BaseModel, Field
from typing import List, Any, Literal, cast

# --- Pydantic Models (Bleiben gleich) ---
class Filter(BaseModel):
    table: str
    column: str
    operator: Literal["==", ">", "<", "like", "in", ">=", "<="]
    value: Any

class DatabaseQuery(BaseModel):
    main_table: str = Field(description="Primärtabelle der Abfrage")
    join_tables: List[str] = Field(default_factory=list)
    filters: List[Filter]
    explanation: str

def load_schema_context() -> str:
    # Navigiert zu source/db/schema.json
    base_path = Path(__file__).resolve().parent.parent
    schema_path = base_path / "db" / "db_schema.json"

    if not schema_path.exists():
        # Fallback für Tests direkt im Services-Ordner
        schema_path = Path(__file__).parent.parent / "db" / "db_schema.json"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    context = "DATENBANK-SCHEMA (Verfügbare Tabellen und Spalten):\n"
    for table, details in schema_data.items():
        columns = ", ".join(details["columns"].keys())
        context += f"- Tabelle: '{table}' | Spalten: [{columns}]\n"
    return context

client = instructor.from_litellm(completion)

def extract_query_intent(user_text: str, model_name: str = "ollama/gemma3:4b") -> DatabaseQuery:
    dynamic_schema = load_schema_context()

    # SCHÄRFERER SYSTEM PROMPT
    system_instruction = (
        f"{dynamic_schema}\n\n"
        "AUFGABE:\n"
        "Du bist ein präziser SQL-Intent-Extraktor. Erstelle einen Abfrageplan basierend auf dem Schema.\n\n"
        "STRIKTE REGELN:\n"
        "1. Nutze für 'main_table' und 'column' EXAKT die Namen aus dem Schema.\n"
        "2. Schreibe Tabellen- und Spaltennamen IMMER komplett klein (lowercase).\n"
        "3. Halluziniere keine Tabellen. Wenn eine Tabelle nicht im Schema ist, nutze die ähnlichste.\n"
        "4. Gib NUR das geforderte JSON-Format zurück, keinen Text davor oder danach."
    )

    try:
        response = client.chat.completions.create(
            model=model_name,
            response_model=DatabaseQuery,
            max_retries=3,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Benutzeranfrage: '{user_text}'"}
            ]
        )
        return cast(DatabaseQuery, response)
    except Exception as e:
        print(f"Fehler bei der Kommunikation mit Ollama ({model_name}): {e}")
        raise

if __name__ == "__main__":
    try:
        # Test mit einer Anfrage, die oft Fehler provoziert
        result = extract_query_intent("Zeig mir alle Rechnungen von Amazon")
        print("\n--- Extrahierter Query-Plan ---")
        print(result.model_dump_json(indent=2))
    except Exception as e:
        print(f"Fehler: {e}")