import os
import time
from source.utils.logger import get_agent_logger

agent_logger = get_agent_logger()


def get_pdf_files(directory: str):
    """Sucht rekursiv nach PDF-Dateien."""

    agent_logger.info(f"Starte PDF-Scan: {directory}")
    scan_start = time.time()

    # Validierung
    if not os.path.exists(directory):
        agent_logger.error(f"Verzeichnis existiert nicht: {directory}")
        return []

    if not os.path.isdir(directory):
        agent_logger.error(f"Pfad ist kein Verzeichnis: {directory}")
        return []

    # PDF-Suche
    pdf_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(directory)
        for f in files if f.lower().endswith('.pdf')
    ]

    scan_time = time.time() - scan_start

    agent_logger.info(
        f"PDF-Scan abgeschlossen: {len(pdf_files)} PDFs gefunden | "
        f"Zeit: {scan_time:.2f}s"
    )

    if pdf_files:
        agent_logger.debug(f"Erste 5 PDFs: {[os.path.basename(f) for f in pdf_files[:5]]}")
    else:
        agent_logger.warning(f"Keine PDFs gefunden in: {directory}")

    return pdf_files
