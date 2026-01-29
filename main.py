import os
import sys
from flask import Flask

# lokale Importe
from source.db.database import init_database, get_model
from source.services.manager import orchestrator
from source.services.processor import process_invoices_from_folder
from source.utils.logger import get_system_logger, get_db_logger, get_agent_logger

# Logger initialisieren
system_logger = get_system_logger()
db_logger = get_db_logger()
agent_logger = get_agent_logger()

# --- KONFIGURATION ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
WATCH_DIRECTORY = os.path.join(BASE_DIR, "source", "Test_Invoices")
DEFAULT_USER = "LokalAdmin"


def main():
    system_logger.info("=" * 60)
    system_logger.info("SmartDesk wird gestartet...")
    system_logger.info(f"Basis-Verzeichnis: {BASE_DIR}")
    system_logger.info(f"Watch-Directory: {WATCH_DIRECTORY}")
    system_logger.info(f"Standard-User: {DEFAULT_USER}")
    system_logger.info("=" * 60)

    # 1. Flask App Setup
    app = Flask(__name__)
    db_path = os.path.join(BASE_DIR, 'smartdesk.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    system_logger.info(f"Flask App konfiguriert")
    db_logger.info(f"Datenbank-Pfad: {db_path}")

    # 2. Datenbank & Dynamische Models initialisieren
    print(f"[System] Initialisiere Datenbank unter: {db_path}")
    try:
        init_database(app)
        db_logger.info("Datenbank erfolgreich initialisiert")
        system_logger.info("✅ Datenbank bereit")
    except Exception as e:
        db_logger.critical(f"Datenbank-Initialisierung fehlgeschlagen: {e}", exc_info=True)
        system_logger.critical(f"[KRITISCH] Datenbank-Fehler: {e}")
        print(f"[Kritisch] Datenbank-Fehler: {e}")
        sys.exit(1)

    # 3. Ordner-Check
    if not os.path.exists(WATCH_DIRECTORY):
        system_logger.warning(f"Watch-Directory existiert nicht, wird erstellt: {WATCH_DIRECTORY}")
        os.makedirs(WATCH_DIRECTORY)
        system_logger.info("Watch-Directory erstellt")
    else:
        system_logger.info(f"Watch-Directory gefunden: {WATCH_DIRECTORY}")

    # 4. START-IMPORT & STATUS-CHECK
    with app.app_context():
        system_logger.info("=" * 60)
        system_logger.info("PHASE 1: INITIAL-SCAN")
        system_logger.info("=" * 60)

        print("\n--- SCHRITT 1: SCANNE ORDNER NACH NEUEN RECHNUNGEN ---")

        try:
            import_stats = process_invoices_from_folder(WATCH_DIRECTORY, DEFAULT_USER)

            system_logger.info("Initial-Scan abgeschlossen")
            system_logger.info(f"Import-Statistik: {import_stats}")

        except Exception as e:
            system_logger.error(f"Fehler beim Initial-Scan: {e}", exc_info=True)
            print(f"[Fehler] Initial-Scan fehlgeschlagen: {e}")

        # NEU: Kontroll-Ausgabe der Datenbank-Inhalte
        try:
            Invoice = get_model("Invoice")
            invoice_count = Invoice.query.count()

            db_logger.info(f"Datenbank-Status: {invoice_count} Rechnungen gespeichert")
            system_logger.info(f"✅ Datenbank-Check: {invoice_count} Rechnungen")

            print(f"[Kontrolle] Aktuell gespeicherte Rechnungen: {invoice_count}")
        except Exception as e:
            db_logger.error(f"Datenbank-Status-Check fehlgeschlagen: {e}", exc_info=True)
            print("[Kontrolle] Konnte Rechnungs-Anzahl nicht prüfen.")

        print("--- IMPORT-PHASE ABGESCHLOSSEN ---\n")
        system_logger.info("=" * 60)
        system_logger.info("PHASE 2: INTERAKTIVER CHAT-MODUS")
        system_logger.info("=" * 60)

    # 5. INTERAKTIVER CHAT-MODUS
    print("=" * 50)
    print(" SMARTDESK KI-ASSISTENT BEREIT")
    print("=" * 50)

    agent_logger.info("Chat-Modus gestartet")
    query_count = 0

    with app.app_context():
        while True:
            try:
                user_query = input("\nDeine Frage: ").strip()

                # Exit-Kommandos
                if user_query.lower() in ["exit", "quit", "q"]:
                    agent_logger.info(f"Chat-Modus beendet durch User (Queries: {query_count})")
                    system_logger.info("SmartDesk wird beendet...")
                    print("\n👋 Auf Wiedersehen!")
                    break

                # Leere Eingabe ignorieren
                if not user_query:
                    continue

                query_count += 1
                agent_logger.info(f"[Query #{query_count}] User-Anfrage: '{user_query[:100]}...'")

                import time
                query_start = time.time()

                # Orchestrator aufrufen
                answer = orchestrator(user_query)

                query_time = time.time() - query_start

                agent_logger.info(
                    f"[Query #{query_count}] Antwort generiert | "
                    f"Zeit: {query_time:.2f}s | "
                    f"Antwort-Länge: {len(answer)} Zeichen"
                )
                agent_logger.debug(f"[Query #{query_count}] Antwort: {answer[:200]}...")

                print(f"\n🤖 ASSISTANT:\n{answer}\n" + "-" * 30)

            except KeyboardInterrupt:
                agent_logger.info(f"Chat-Modus durch Ctrl+C beendet (Queries: {query_count})")
                system_logger.info("SmartDesk durch User-Interrupt beendet")
                print("\n\n👋 Auf Wiedersehen!")
                break

            except Exception as e:
                agent_logger.error(f"[Query #{query_count}] Fehler: {e}", exc_info=True)
                print(f"\n[Fehler im Chat]: {e}")
                print("Bitte versuche es erneut oder tippe 'exit' zum Beenden.\n")

    # Abschluss-Log
    system_logger.info("=" * 60)
    system_logger.info("SmartDesk wurde beendet")
    system_logger.info(f"Gesamt-Queries in dieser Session: {query_count}")
    system_logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        system_logger.critical(f"Unerwarteter Fehler in main(): {e}", exc_info=True)
        print(f"\n[KRITISCHER FEHLER]: {e}")
        sys.exit(1)
