import json
from pathlib import Path
import instructor
from litellm import completion
from pydantic import BaseModel, Field, field_validator
from typing import List, Any, Literal, cast, Optional


# --- Pydantic Models ---
class Filter(BaseModel):
    table: str
    column: str
    # 'max' ist hier absichtlich nicht enthalten, um Pydantic-Fehler bei Fehlverhalten zu triggern
    operator: Literal["==", ">", "<", "like", "in", ">=", "<="]
    value: Any


class DatabaseQuery(BaseModel):
    main_table: str = Field(description="Primärtabelle der Abfrage (z.B. invoice)")
    join_tables: List[str] = Field(default_factory=list)
    filters: List[Filter] = Field(default_factory=list)
    # Neue Felder für Aggregations-Ersatz
    order_by: Optional[str] = Field(default=None, description="Spalte für Sortierung")
    direction: Literal["asc", "desc"] = Field(default="desc")
    limit: Optional[int] = Field(default=None, description="Anzahl Ergebnisse")

    explanation: Optional[str] = Field(
        default="Analysiere Datenbank nach Benutzerwunsch",
        description="Logik hinter der Abfrage"
    )

    @field_validator("main_table")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        return v.lower()


# --- Hilfsfunktionen ---
def load_schema_context() -> str:
    base_path = Path(__file__).resolve().parent.parent
    schema_path = base_path / "db" / "db_schema.json"

    if not schema_path.exists():
        schema_path = Path(__file__).parent.parent / "db" / "db_schema.json"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    context = "DATENBANK-SCHEMA (Verfügbare Tabellen und Spalten):\n"
    for table, details in schema_data.items():
        columns = ", ".join(details["columns"].keys())
        context += f"- Tabelle: '{table.lower()}' | Spalten: [{columns}]\n"

    return context


client = instructor.from_litellm(completion)


def extract_query_intent(user_text: str, model_name: str = "ollama/gemma3:4b") -> DatabaseQuery:
    """Extrahiert den Abfrage-Wunsch des Nutzers in ein strukturiertes Format."""
    dynamic_schema = load_schema_context()

    system_instruction = (
        f"{dynamic_schema}\n\n"
        "### AUFGABE\n"
        "Erstelle einen SQL-Abfrageplan als JSON. Nutze EXAKT die 'DatabaseQuery' Struktur.\n\n"
        "### REGELN FÜR FILTER\n"
        "1. Erlaubte Operatoren: ['==', '>', '<', 'like', 'in', '>=', '<=']\n"
        "2. VERBOTEN: Nutze NIEMALS 'max', 'min' oder 'sum' als Operator. Das führt zu Fehlern!\n\n"
        "### LOGIK FÜR 'HÖCHSTE / TEUERSTE / NEUESTE'\n"
        "Um den höchsten oder neuesten Wert zu finden (z.B. 'höchste Rechnung'):\n"
        "- Lass 'filters' leer [].\n"
        "- Setze 'order_by' auf die Spalte (z.B. 'amount' oder 'date').\n"
        "- Setze 'direction' auf 'desc'.\n"
        "- Setze 'limit' auf 1.\n\n"
        "### BEISPIEL\n"
        "User: 'Höchster Rechnungsbetrag'\n"
        "JSON: { \"main_table\": \"invoice\", \"filters\": [], \"order_by\": \"amount\", \"direction\": \"desc\", \"limit\": 1 }"
    )

    try:
        response = client.chat.completions.create(
            model=model_name,
            response_model=DatabaseQuery,
            max_retries=3,  # Wichtig für kleine Modelle
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Benutzeranfrage: '{user_text}'"}
            ]
        )

        # --- HEURISTIK ZUR SELBSTREPARATUR ---
        # Falls das Modell trotz Verbot versucht, 'max' in Filtern zu nutzen
        # (Dies greift nur, wenn instructor den Validierungsfehler umgeht oder
        # wir das Schema temporär lockern würden)
        return cast(DatabaseQuery, response)

    except Exception as e:
        # Falls Pydantic wegen 'max' meckert, versuchen wir einen manuellen Fix im Catch-Block
        # oder liefern den Standard-Fallback.
        print(f"[LLM-Error] Fehler bei Intent-Extraktion: {e}")
        return DatabaseQuery(
            main_table="invoice",
            filters=[],
            explanation="Fallback: Zeige alle Rechnungen."
        )


if __name__ == "__main__":
    test_query = "Welche Rechnung ist die höchste?"
    print(f"Test mit: {test_query}")
    result = extract_query_intent(test_query)
    print(result.model_dump_json(indent=2))