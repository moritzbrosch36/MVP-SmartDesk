from typing import List
import logging

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

    for f in query_plan.filters:
        col_name = f.column.lower()

        # NEU: Sicherheits-Check gegen halluzinierte technische IDs
        # Wenn das LLM versucht nach user_id mit einem Dict zu filtern, ignorieren wir das im MVP.
        if col_name == "user_id" and isinstance(f.value, dict):
            logging.info("Ignoriere technischen user_id Filter (Dictionary-Bereinigung).")
            continue

        if hasattr(SqlModel, col_name):
            column = getattr(SqlModel, col_name)
            val = f.value

            # Bereinigung falls doch noch ein Dict durchrutscht
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
                if not isinstance(val, list):
                    val = [val]
                query = query.filter(column.in_(val))
        else:
            logging.warning(f"Spalte '{col_name}' nicht in '{registry_key}' gefunden.")

    db_results = query.all()
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