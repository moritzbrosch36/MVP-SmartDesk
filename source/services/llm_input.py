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
    operator: Literal["==", ">", "<", "like", "in", ">=", "<="]
    value: Any


class DatabaseQuery(BaseModel):
    main_table: str = Field(description="Primärtabelle der Abfrage (z.B. invoice)")
    join_tables: List[str] = Field(default_factory=list)
    filters: List[Filter] = Field(default_factory=list)
    explanation: Optional[str] = Field(
        default="Analysiere Datenbank nach Benutzerwunsch",
        description="Logik hinter der Abfrage"
    )

    @field_validator("main_table")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        # Zwingt den Tabellennamen in Kleinschreibung,
        # passend zur Logik im Extractor/Schema
        return v.lower()


# --- Hilfsfunktionen ---
def load_schema_context() -> str:
    """Lädt das Schema und bereitet es für den System-Prompt auf."""
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
        "AUFGABE:\n"
        "Erstelle einen SQL-Abfrageplan als JSON basierend auf dem Schema.\n\n"
        "STRIKTE REGELN:\n"
        "1. main_table MUSS eine der oben genannten Tabellen sein (meist 'invoice').\n"
        "2. filters darf NUR gefüllt werden, wenn der User nach speziellen Werten fragt.\n"
        "3. Nutze 'like' nur für Textsuche, '==' für exakte Übereinstimmung.\n"
        "4. Setze NIEMALS Platzhalter wie '%' als Wert ein, wenn der User nicht danach fragt.\n"
        "5. Wenn der User nur allgemein fragt ('Zeig mir Rechnungen'), lass 'filters' leer [].\n"
    )

    try:
        # Mode JSON sorgt dafür, dass Gemma3 stabileres JSON liefert
        response = client.chat.completions.create(
            model=model_name,
            response_model=DatabaseQuery,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Benutzeranfrage: '{user_text}'"}
            ]
        )
        return cast(DatabaseQuery, response)

    except Exception as e:
        print(f"[LLM-Error] Fehler bei Intent-Extraktion: {e}")
        # Sicherer Fallback: Zeige einfach alle Rechnungen des Users
        return DatabaseQuery(
            main_table="invoice",
            filters=[],
            explanation="Fallback aufgrund eines Verarbeitungsfehlers."
        )


if __name__ == "__main__":
    # Schneller Testlauf
    test_query = "Welche Rechnungen habe ich?"
    print(f"Test mit: {test_query}")
    print(extract_query_intent(test_query).model_dump_json(indent=2))