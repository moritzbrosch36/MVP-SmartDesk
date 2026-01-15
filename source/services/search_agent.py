from typing import List

from source.services.llm_input import DatabaseQuery
from source.models.user import UserRead
from source.models.file_data import FileDataRead
from source.models.invoice import InvoiceRead

# Mapping von Tabellenname zu Pydantic-Model
# Wichtig: Alles kleingeschrieben, passend zur Normalisierung im Manager
MODEL_MAP = {
    "user": UserRead,
    "file_data": FileDataRead,
    "invoice": InvoiceRead,
    "invoices": InvoiceRead
}


def database_agent(query_plan: DatabaseQuery) -> List:
    """
    Diese Woche: Simuliert die DB-Abfrage.
    Nächste Woche: Hier kommt die echte SQL-Logik rein.
    """
    table_name = query_plan.main_table.lower()
    target_model = MODEL_MAP.get(table_name)

    if not target_model:
        raise ValueError(f"Tabelle '{table_name}' existiert nicht.")

    # --- SIMULATION DER SUCHE ---
    # Wir schauen uns an, was der Nutzer gesucht hat (z.B. 'Amazon')
    search_value = ""
    if query_plan.filters:
        # Wir nehmen einfach den Wert des ersten Filters für die Demo
        search_value = str(query_plan.filters[0].value).lower()

    # Wir erstellen eine Liste mit Dummy-Daten
    all_mock_data = {
        "invoice": [
            {"id": 1, "company": "Amazon", "amount": 120.50, "invoice_number": "INV-001", "due_date": "2026-02-01",
             "user_id": 1, "file_data_id": 1},
            {"id": 2, "company": "Apple", "amount": 999.00, "invoice_number": "INV-002", "due_date": "2026-03-15",
             "user_id": 1, "file_data_id": 2},
        ]
    }

    # Filtern simulieren
    results = []
    data_list = all_mock_data.get(table_name, [])

    for item in data_list:
        if not search_value or search_value in item.get("company", "").lower():
            # 1. Der User der Rechnung
            mock_user = {
                "id": 1,
                "name": "Test User",
                "created_at": "2026-01-01T10:00:00"
            }

            item["user"] = mock_user
            item["created_at"] = "2026-01-01T10:00:00"
            item["updated_at"] = "2026-01-01T10:00:00"

            # 2. Die Dateidaten inkl. dem User der Datei (WICHTIG!)
            item["file_data"] = {
                "id": 1,
                "user_id": 1,
                "filename": "test.pdf",
                "file_path": "/tmp",
                "file_type": "pdf",
                "created_at": "2026-01-01T10:00:00",
                "updated_at": "2026-01-01T10:00:00",
                "user": mock_user  # <-- DIES hat gefehlt!
            }

            results.append(target_model(**item))

    return results