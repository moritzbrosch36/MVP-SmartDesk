from litellm import completion
import logging


def generate_final_response(original_query: str, db_results: list) -> str:
    """
    LLM 2: Der Kommunikator. Er nimmt die technischen Daten aus der DB
    und macht daraus eine menschliche Antwort.
    """

    # Datenaufbereitung
    if not db_results:
        data_context = "HINWEIS: Es wurden keine Einträge in der Datenbank gefunden."
    else:
        try:
            # Wir wandeln die Pydantic-Objekte in JSON-Strings um.
            # Da deine Models (UserRead, InvoiceRead) model_dump_json() unterstützen,
            # bekommt das LLM alle Details in einem strukturierten Format.
            data_context = "\n".join([obj.model_dump_json() for obj in db_results])
        except Exception as e:
            logging.error(f"Fehler bei der Serialisierung der DB-Ergebnisse: {e}")
            data_context = str(db_results)  # Fallback auf einfachen String

    system_instruction = (
        "Du bist die Stimme eines intelligenten Dokumenten-Assistenten. "
        "Deine Aufgabe ist es, die technischen Suchergebnisse der Datenbank "
        "in eine natürliche, hilfreiche Antwort zu übersetzen."
        "\n\nVERHALTENSREGELN:"
        "- Wenn Daten da sind: Fasse sie präzise und freundlich zusammen."
        "- Wenn keine Daten da sind: Entschuldige dich höflich."
        "- Erfinde NIEMALS Fakten dazu (Halluzinations-Schutz)."
        "- Antworte immer auf Deutsch."
    )

    prompt = f"""
    NUTZERANFRAGE: {original_query}

    GEFUNDENE DATENBANK-DATEN (JSON-Format):
    {data_context}

    Bitte antworte dem Nutzer basierend auf diesen Daten:
    """

    # Hier nutzen wir das gleiche Modell wie in LLM1
    response = completion(
        model="ollama/gemma3:4b",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7  # Ein bisschen Kreativität für natürlichere Sprache
    )

    return response.choices[0].message.content
