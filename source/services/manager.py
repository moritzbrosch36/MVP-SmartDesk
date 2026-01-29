import logging

from source.services.llm_input import extract_query_intent
from source.services.llm_output import generate_final_response
from source.services.search_agent import database_agent


def orchestrator(user_input: str):
    """
    Der Dirigent deines MVPs. Er steuert den Datenfluss
    zwischen KI-Logik und Datenbank-Agent.
    """
    print(f"\n--- 🚀 Starte Verarbeitung: {user_input} ---")

    try:
        # 1. SCHRITT: LLM 1 (Verständnis & Planung)
        print("[System] Rufe LLM 1 (Gemma 3) zur Intent-Extraktion auf...")
        query_plan = extract_query_intent(user_input)

        # --- FIX: NORMALISIERUNG ---
        # Erzwingen Kleinschreibung für die Tabelle, damit 'Invoice' zu 'invoice' wird.
        # Das verhindert den Fehler "Kein Model für Tabelle gefunden".
        query_plan.main_table = query_plan.main_table.lower()

        # Auch die Filter-Spalten sollten zur Sicherheit normalisiert werden
        for f in query_plan.filters:
            f.column = f.column.lower()
        # ----------------------------

        print(f"[LLM 1] Plan: Tabelle '{query_plan.main_table}' | Filter: {query_plan.filters}")

        # 2. SCHRITT: AGENT (Ausführung)
        print("[System] Agent sucht Daten in der Datenbank...")
        db_results = database_agent(query_plan)
        print(f"[Agent] Erfolgreich {len(db_results)} Datensätze geladen.")

        # 3. SCHRITT: LLM 2 (Kommunikation)
        print("[System] Rufe LLM 2 (Gemma 3) für die finale Antwort auf...")
        final_answer = generate_final_response(
            original_query=user_input,
            db_results=db_results
        )

        return final_answer

    except Exception as e:
        # Zentrales Error-Handling für den MVP-Flow
        error_msg = f"Fehler im Orchestrator: {str(e)}"
        logging.error(error_msg)
        # Wir geben eine hilfreiche Nachricht zurück, falls die DB-Tabelle wirklich fehlt
        if "Kein Model für Tabelle" in str(e):
            return f"Fehler: Ich konnte die Tabelle '{query_plan.main_table}' nicht im System finden."
        return "Entschuldigung, ich hatte ein Problem beim Verarbeiten Ihrer Anfrage."


# TEST-DURCHLAUF
if __name__ == "__main__":
    # Teste mit Amazon, Apple und Microsoft (Microsoft hat keine Rechnungen)
    answer = orchestrator("Zeig mir alle Rechnungen von Amazon")
    print("\n--- 🤖 ASSISTANT ---")
    print(answer)