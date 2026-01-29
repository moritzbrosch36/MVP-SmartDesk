import os
import time
from datetime import date
from source.db.database import db, is_hash_processed, calculate_file_hash
from source.services.scanner import get_pdf_files
from source.services.classifier import is_invoice
from source.services.extractor import extract_invoice_data
from source.repositories.file_repository import save_file
from source.repositories.invoice_repository import get_or_create_invoice
from source.repositories.user_repository import get_or_create_user
from source.utils.logger import get_db_logger, get_agent_logger

db_logger = get_db_logger()
agent_logger = get_agent_logger()


def process_invoices_from_folder(directory_path: str, user_name: str):
    agent_logger.info(f"=== Starte Import-Vorgang ===")
    user = get_or_create_user(user_name)
    files = get_pdf_files(directory_path)
    stats = {"processed": 0, "skipped": 0, "errors": 0}

    for idx, file_path in enumerate(files, 1):
        file_name = os.path.basename(file_path)

        # --- SCHRITT 1: HASH BERECHNEN & PRÜFEN ---
        f_hash = calculate_file_hash(file_path)
        if is_hash_processed(f_hash):
            print(f"[Skip] Datei bereits bekannt (Hash): {file_name}")
            stats["skipped"] += 1
            continue

        try:
            # --- SCHRITT 2: KLASSIFIZIERUNG ---
            if not is_invoice(file_path):
                print(f"[Ignoriert] Keine Rechnung: {file_name}")
                stats["skipped"] += 1
                continue

            # --- SCHRITT 3: KI EXTRAKTION (TEUER) ---
            print(f"[Extraktion] Analysiere {file_name}...")
            invoice_data = extract_invoice_data(file_path)
            if not invoice_data:
                stats["errors"] += 1
                continue

            # --- SCHRITT 4: SPEICHERN ---
            file_entry = save_file(
                user_id=user.id, filename=file_name,
                file_path=file_path, file_type="pdf", file_hash=f_hash
            )

            invoice = get_or_create_invoice(
                user_id=user.id, file_data_id=file_entry.id,
                company=invoice_data.get("company", "Unbekannt"),
                invoice_number=str(invoice_data.get("invoice_number", "FEHLT")),
                due_date=invoice_data.get("due_date") or date.today(),
                amount=float(invoice_data.get("amount") or 0.0),
                invoice_hash=f_hash  # Wir nutzen den File-Hash auch hier
            )
            print(f"[Erfolg] Gespeichert: {invoice.invoice_number}")
            stats["processed"] += 1

        except Exception as e:
            db.session.rollback()
            stats["errors"] += 1

    return stats