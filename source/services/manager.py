import logging
from source.services.llm_input import extract_query_intent
from source.services.llm_output import generate_final_response
from source.services.search_agent import database_agent


def orchestrator(user_input: str):
    """
    Steuert den Datenfluss: LLM 1 (Planung) -> Agent (Abfrage) -> LLM 2 (Antwort).
    """
    print(f"\n--- 🚀 Starte Verarbeitung: {user_input} ---")

    try:
        # 1. SCHRITT: LLM 1 (Verständnis & Planung)
        print("[System] Rufe LLM 1 (Gemma 3) zur Intent-Extraktion auf...")
        query_plan = extract_query_intent(user_input)

        # Normalisierung (Zwingend für den Datenbank-Registry-Look-up)
        query_plan.main_table = query_plan.main_table.lower()
        for f in query_plan.filters:
            f.column = f.column.lower()

        # Sortier-Feld ebenfalls normalisieren
        if hasattr(query_plan, 'order_by') and query_plan.order_by:
            query_plan.order_by = query_plan.order_by.lower()

        print(
            f"[LLM 1] Plan: Tabelle '{query_plan.main_table}' | Sortierung: {query_plan.order_by} | Limit: {query_plan.limit}")

        # 2. SCHRITT: AGENT (Ausführung mit Sorting & Limit)
        print("[System] Agent sucht Daten in der Datenbank...")
        db_results = database_agent(query_plan)
        print(f"[Agent] Erfolgreich {len(db_results)} Datensätze geladen.")

        # 3. SCHRITT: LLM 2 (Kommunikation der Ergebnisse)
        print("[System] Rufe LLM 2 (Gemma 3) für die finale Antwort auf...")
        final_answer = generate_final_response(
            original_query=user_input,
            db_results=db_results
        )

        return final_answer

    except Exception as e:
        error_msg = f"Fehler im Orchestrator: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return "Entschuldigung, ich hatte ein Problem beim Verarbeiten Ihrer Anfrage."