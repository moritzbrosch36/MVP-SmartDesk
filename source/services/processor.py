import os
import time
from datetime import date
from source.db.database import db
from source.services.scanner import get_pdf_files
from source.services.classifier import is_invoice
from source.services.extractor import extract_invoice_data
from source.repositories.file_repository import save_file
from source.repositories.invoice_repository import get_or_create_invoice
from source.repositories.user_repository import get_or_create_user
from source.utils.logger import get_db_logger, get_agent_logger

# Logger initialisieren
db_logger = get_db_logger()
agent_logger = get_agent_logger()  # Für den gesamten Workflow


def process_invoices_from_folder(directory_path: str, user_name: str):
    """
    Steuert den gesamten Workflow:
    Scan -> Filter (Hybrid) -> Extraction (AI via Schema) -> Database (SQL)
    """
    agent_logger.info(f"=== Starte Import-Vorgang ===")
    agent_logger.info(f"Verzeichnis: {directory_path}")
    agent_logger.info(f"User: {user_name}")

    workflow_start = time.time()

    print(f"\n--- Starte Import-Vorgang ---")
    print(f"Verzeichnis: {directory_path}")

    # 1. User sicherstellen (Zentraler Anker für alle Daten)
    try:
        user_start = time.time()
        user = get_or_create_user(user_name)
        user_time = time.time() - user_start

        db_logger.info(f"User geladen/erstellt: {user_name} (ID: {user.id}) [{user_time:.2f}s]")
        agent_logger.debug(f"User-ID: {user.id}")

    except Exception as e:
        agent_logger.error(f"User konnte nicht geladen/erstellt werden: {user_name} - {e}", exc_info=True)
        print(f"[Abbruch] Konnte User nicht laden/erstellen: {e}")
        db.session.rollback()
        return {"processed": 0, "skipped": 0, "errors": 1}

    # 2. Dateien finden
    scan_start = time.time()
    files = get_pdf_files(directory_path)
    scan_time = time.time() - scan_start

    agent_logger.info(f"PDF-Scan abgeschlossen: {len(files)} Dateien gefunden [{scan_time:.2f}s]")
    print(f"Gefunden: {len(files)} PDF-Dateien.")

    stats = {"processed": 0, "skipped": 0, "errors": 0}

    for idx, file_path in enumerate(files, 1):
        file_name = os.path.basename(file_path)
        file_start = time.time()

        agent_logger.info(f"[{idx}/{len(files)}] Verarbeite: {file_name}")

        try:
            # 3. Hybride Klassifizierung
            if not is_invoice(file_path):
                agent_logger.info(f"Übersprungen (keine Rechnung): {file_name}")
                print(f"[Ignoriert] Dokument ist keine Rechnung: {file_name}")
                stats["skipped"] += 1
                continue

            # 4. Datenextraktion
            print(f"[Extraktion] Analysiere {file_name} mit Gemma3...")
            invoice_data = extract_invoice_data(file_path)

            if not invoice_data:
                agent_logger.warning(f"Extraktion fehlgeschlagen: {file_name}")
                print(f"[Fehler] KI konnte keine validen Daten extrahieren: {file_name}")
                stats["errors"] += 1
                continue

            # --- VALIDIERUNG DER PFLICHTFELDER ---
            clean_due_date = invoice_data.get("due_date")
            if not clean_due_date:
                clean_due_date = date.today()
                agent_logger.warning(f"Kein Fälligkeitsdatum für {file_name}, nutze heute: {clean_due_date}")
                print(f"[Info] Kein Fälligkeitsdatum gefunden für {file_name}. Nutze heute.")

            # 5. Speichern in SQL
            db_start = time.time()

            file_entry = save_file(
                user_id=user.id,
                filename=file_name,
                file_path=file_path,
                file_type="pdf"
            )
            db_logger.debug(f"File-Entry erstellt: {file_name} (ID: {file_entry.id})")

            # Speichert Rechnungsdaten & prüft auf inhaltliche Dubletten
            invoice = get_or_create_invoice(
                user_id=user.id,
                file_data_id=file_entry.id,
                company=invoice_data.get("company") or "Unbekannte Firma",
                invoice_number=str(invoice_data.get("invoice_number") or "FEHLT"),
                due_date=clean_due_date,
                issue_date=invoice_data.get("issue_date"),
                amount=float(invoice_data.get("amount") or 0.0),
                currency=invoice_data.get("currency") or "EUR",
                description=invoice_data.get("description") or "Automatischer KI-Import"
            )

            db_time = time.time() - db_start
            file_time = time.time() - file_start

            db_logger.info(
                f"Rechnung gespeichert: {invoice.invoice_number} | "
                f"Firma: {invoice.company} | "
                f"Betrag: {invoice.amount} {invoice.currency} | "
                f"DB-Zeit: {db_time:.2f}s"
            )
            agent_logger.info(
                f"[{idx}/{len(files)}] Erfolgreich: {file_name} | "
                f"Gesamtzeit: {file_time:.2f}s"
            )

            print(f"[Erfolg] Datenbank-Eintrag erstellt: {invoice.invoice_number} ({invoice.company})")
            stats["processed"] += 1

        except Exception as e:
            file_time = time.time() - file_start
            agent_logger.error(
                f"Kritischer Fehler bei {file_name}: {str(e)} | "
                f"Zeit bis Fehler: {file_time:.2f}s",
                exc_info=True
            )
            print(f"[Kritischer Fehler] Fehler bei Verarbeitung von {file_name}: {str(e)}")
            stats["errors"] += 1

            # --- WICHTIG: SESSION REINIGEN ---
            db.session.rollback()
            db_logger.warning(f"Datenbank-Session zurückgesetzt nach Fehler bei {file_name}")
            print(f"[System] Datenbank-Sitzung zurückgesetzt.")

    # FINALE STATISTIKEN
    workflow_time = time.time() - workflow_start

    agent_logger.info("=" * 50)
    agent_logger.info(f"IMPORT ABGESCHLOSSEN | Gesamtzeit: {workflow_time:.2f}s")
    agent_logger.info(f"Erfolgreich: {stats['processed']}")
    agent_logger.info(f"Übersprungen: {stats['skipped']}")
    agent_logger.info(f"Fehlerhaft: {stats['errors']}")
    agent_logger.info(f"Durchschnitt pro Datei: {workflow_time / len(files):.2f}s")
    agent_logger.info("=" * 50)

    print("\n" + "=" * 40)
    print(f"IMPORT ABGESCHLOSSEN")
    print(f"- Erfolgreich: {stats['processed']}")
    print(f"- Übersprungen: {stats['skipped']}")
    print(f"- Fehlerhaft: {stats['errors']}")
    print("=" * 40)

    return stats