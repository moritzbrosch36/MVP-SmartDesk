import os
import sys
from flask import Flask

# lokale Importe
from source.db.database import init_database, get_model
from source.services.manager import orchestrator
from source.services.processor import process_invoices_from_folder

# --- KONFIGURATION ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
WATCH_DIRECTORY = os.path.join(BASE_DIR, "source", "Test_Invoices")
DEFAULT_USER = "LokalAdmin"


def main():
    # 1. Flask App Setup
    app = Flask(__name__)
    db_path = os.path.join(BASE_DIR, 'smartdesk.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 2. Datenbank & Dynamische Models initialisieren
    print(f"[System] Initialisiere Datenbank unter: {db_path}")
    try:
        init_database(app)
    except Exception as e:
        print(f"[Kritisch] Datenbank-Fehler: {e}")
        sys.exit(1)

    # 3. Ordner-Check
    if not os.path.exists(WATCH_DIRECTORY):
        os.makedirs(WATCH_DIRECTORY)

    # 4. START-IMPORT & STATUS-CHECK
    with app.app_context():
        print("\n--- SCHRITT 1: SCANNE ORDNER NACH NEUEN RECHNUNGEN ---")
        process_invoices_from_folder(WATCH_DIRECTORY, DEFAULT_USER)

        # NEU: Kontroll-Ausgabe der Datenbank-Inhalte
        try:
            Invoice = get_model("Invoice")
            invoice_count = Invoice.query.count()
            print(f"[Kontrolle] Aktuell gespeicherte Rechnungen: {invoice_count}")
        except Exception:
            print("[Kontrolle] Konnte Rechnungs-Anzahl nicht prüfen.")

        print("--- IMPORT-PHASE ABGESCHLOSSEN ---\n")

    # 5. INTERAKTIVER CHAT-MODUS
    print("=" * 50)
    print(" SMARTDESK KI-ASSISTENT BEREIT")
    print("=" * 50)

    with app.app_context():
        while True:
            try:
                user_query = input("\nDeine Frage: ").strip()
                if user_query.lower() in ["exit", "quit", "q"]:
                    break
                if not user_query:
                    continue

                answer = orchestrator(user_query)
                print(f"\n🤖 ASSISTANT:\n{answer}\n" + "-" * 30)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n[Fehler im Chat]: {e}")


if __name__ == "__main__":
    main()