import logging
import sys
from pathlib import Path
from datetime import datetime

# Log-Verzeichnis erstellen
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Dateiname mit Timestamp
LOG_FILE = LOG_DIR / f"smartdesk_{datetime.now().strftime('%Y%m%d')}.log"


def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Erstellt einen konfigurierten Logger für ein Modul.

    Args:
        name: Name des Loggers (z.B. 'smartdesk.classifier')
        level: Log-Level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Konfigurierter Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Verhindere doppelte Handler
    if logger.handlers:
        return logger

    # Format für Log-Nachrichten
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler 1: Datei (alle Logs)
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Handler 2: Console (nur INFO und höher)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Vordefinierte Logger für verschiedene Module
def get_classifier_logger():
    return setup_logger('smartdesk.classifier')


def get_llm_logger():
    return setup_logger('smartdesk.llm')


def get_db_logger():
    return setup_logger('smartdesk.database')


def get_pdf_logger():
    return setup_logger('smartdesk.pdf')


def get_agent_logger():
    return setup_logger('smartdesk.agent')