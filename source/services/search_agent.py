from typing import List
import logging
from sqlalchemy import desc, asc  # Wichtig für die Sortierung

from source.db.database import get_model
from source.services.llm_input import DatabaseQuery
from source.models import UserRead, FileDataRead, InvoiceRead

PYDANTIC_MAP = {
    "user": UserRead,
    "file_data": FileDataRead,
    "invoice": InvoiceRead,
    "invoices": InvoiceRead
}

REGISTRY_MAP = {
    "user": "User",
    "file_data": "FileData",
    "invoice": "Invoice",
    "invoices": "Invoice"
}


def database_agent(query_plan: DatabaseQuery) -> List:
    table_name = query_plan.main_table.lower()
    registry_key = REGISTRY_MAP.get(table_name)

    if not registry_key:
        raise ValueError(f"Tabelle '{table_name}' nicht definiert.")

    try:
        SqlModel = get_model(registry_key)
    except ValueError as e:
        logging.error(f"Konnte Model {registry_key} nicht finden: {e}")
        raise ValueError(f"Tabelle '{registry_key}' existiert nicht.")

    query = SqlModel.query

    # --- 1. Filter verarbeiten ---
    for f in query_plan.filters:
        col_name = f.column.lower()
        if col_name == "user_id" and isinstance(f.value, dict):
            logging.info("Ignoriere technischen user_id Filter (Dictionary-Bereinigung).")
            continue

        if hasattr(SqlModel, col_name):
            column = getattr(SqlModel, col_name)
            val = f.value
            if isinstance(val, dict):
                val = val.get("value") or val.get("id") or list(val.values())[-1]

            if f.operator == "==":
                query = query.filter(column == val)
            elif f.operator == "like":
                query = query.filter(column.ilike(f"%{val}%"))
            elif f.operator == ">":
                query = query.filter(column > val)
            elif f.operator == "<":
                query = query.filter(column < val)
            elif f.operator == ">=":
                query = query.filter(column >= val)
            elif f.operator == "<=":
                query = query.filter(column <= val)
            elif f.operator == "in":
                if not isinstance(val, list): val = [val]
                query = query.filter(column.in_(val))
        else:
            logging.warning(f"Spalte '{col_name}' nicht in '{registry_key}' gefunden.")

    # --- 2. Sortierung anwenden (NEU) ---
    if hasattr(query_plan, 'order_by') and query_plan.order_by:
        col_name = query_plan.order_by.lower()
        if hasattr(SqlModel, col_name):
            column = getattr(SqlModel, col_name)
            if query_plan.direction == "desc":
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        else:
            logging.warning(f"Sortier-Spalte '{col_name}' nicht gefunden.")

    # --- 3. Limit anwenden (NEU) ---
    if hasattr(query_plan, 'limit') and query_plan.limit:
        query = query.limit(query_plan.limit)

    # Abfrage ausführen
    db_results = query.all()

    # --- 4. Umwandlung in Pydantic Modelle ---
    TargetPydantic = PYDANTIC_MAP.get(table_name)
    if not TargetPydantic:
        return db_results

    final_results = []
    for row in db_results:
        try:
            final_results.append(TargetPydantic.model_validate(row))
        except Exception as e:
            logging.error(f"Validierungsfehler ID {row.id}: {e}")
            continue

    return final_results