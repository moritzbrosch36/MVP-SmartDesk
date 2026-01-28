import os
from datetime import date
from source.db.database import db  # WICHTIG für das Rollback
from source.services.scanner import get_pdf_files
from source.services.classifier import is_invoice
from source.services.extractor import extract_invoice_data
from source.repositories.file_repository import save_file
from source.repositories.invoice_repository import get_or_create_invoice
from source.repositories.user_repository import get_or_create_user

def process_invoices_from_folder(directory_path: str, user_name: str):
    """
    Steuert den gesamten Workflow:
    Scan -> Filter (Hybrid) -> Extraction (AI via Schema) -> Database (SQL)
    """
    print(f"\n--- Starte Import-Vorgang ---")
    print(f"Verzeichnis: {directory_path}")

    # 1. User sicherstellen (Zentraler Anker für alle Daten)
    try:
        user = get_or_create_user(user_name)
    except Exception as e:
        print(f"[Abbruch] Konnte User nicht laden/erstellen: {e}")
        db.session.rollback()
        return {"processed": 0, "skipped": 0, "errors": 1}

    # 2. Dateien finden
    files = get_pdf_files(directory_path)
    print(f"Gefunden: {len(files)} PDF-Dateien.")

    stats = {"processed": 0, "skipped": 0, "errors": 0}

    for file_path in files:
        file_name = os.path.basename(file_path)

        try:
            # 3. Hybride Klassifizierung
            if not is_invoice(file_path):
                print(f"[Ignoriert] Dokument ist keine Rechnung: {file_name}")
                stats["skipped"] += 1
                continue

            # 4. Datenextraktion
            print(f"[Extraktion] Analysiere {file_name} mit Gemma3...")
            invoice_data = extract_invoice_data(file_path)

            if not invoice_data:
                print(f"[Fehler] KI konnte keine validen Daten extrahieren: {file_name}")
                stats["errors"] += 1
                continue

            # --- VALIDIERUNG DER PFLICHTFELDER ---
            # Falls Gemma3 kein Datum findet, setzen wir ein Fallback,
            # um den NOT NULL Constraint Fehler in SQL zu vermeiden.
            clean_due_date = invoice_data.get("due_date")
            if not clean_due_date:
                # Nutze das aktuelle Datum als Notlösung
                clean_due_date = date.today()
                print(f"[Info] Kein Fälligkeitsdatum gefunden für {file_name}. Nutze heute.")

            # 5. Speichern in SQL
            file_entry = save_file(
                user_id=user.id,
                filename=file_name,
                file_path=file_path,
                file_type="pdf"
            )

            # Speichert Rechnungsdaten & prüft auf inhaltliche Dubletten
            invoice = get_or_create_invoice(
                user_id=user.id,
                file_data_id=file_entry.id,
                company=invoice_data.get("company") or "Unbekannte Firma",
                invoice_number=str(invoice_data.get("invoice_number") or "FEHLT"),
                due_date=clean_due_date, # Validierter Wert
                issue_date=invoice_data.get("issue_date"),
                amount=float(invoice_data.get("amount") or 0.0),
                currency=invoice_data.get("currency") or "EUR",
                description=invoice_data.get("description") or "Automatischer KI-Import"
            )

            print(f"[Erfolg] Datenbank-Eintrag erstellt: {invoice.invoice_number} ({invoice.company})")
            stats["processed"] += 1

        except Exception as e:
            print(f"[Kritischer Fehler] Fehler bei Verarbeitung von {file_name}: {str(e)}")
            stats["errors"] += 1
            # --- WICHTIG: SESSION REINIGEN ---
            # Macht die fehlgeschlagene Transaktion rückgängig, damit die Session
            # für die nächste Datei wieder bereit ist.
            db.session.rollback()
            print(f"[System] Datenbank-Sitzung zurückgesetzt.")

    print("\n" + "=" * 40)
    print(f"IMPORT ABGESCHLOSSEN")
    print(f"- Erfolgreich: {stats['processed']}")
    print(f"- Übersprungen: {stats['skipped']}")
    print(f"- Fehlerhaft: {stats['errors']}")
    print("=" * 40)

    return stats