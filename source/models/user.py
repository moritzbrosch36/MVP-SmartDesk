from __future__ import annotations
from typing import List, TYPE_CHECKING
from .base_schema import BaseSchema, Field, datetime

# 1. TYPE_CHECKING: Ermöglicht Autocomplete ohne Laufzeit-Zyklen
if TYPE_CHECKING:
    from .file_data import FileDataRead
    from .invoice import InvoiceRead

# --- Schemas für die Erstellung ---
class UserCreate(BaseSchema):
    name: str = Field(..., max_length=100)

# --- Schemas für das Auslesen ---
class UserRead(UserCreate):
    id: int
    created_at: datetime

    # 2. Nutzung von Strings für die Listen-Beziehungen
    file: List["FileDataRead"] = []
    invoices: List["InvoiceRead"] = []

# --- Pydantic "Heilung" ---
# Hier werden die Abhängigkeiten aufgelöst, sobald alle Dateien geladen sind.
if not TYPE_CHECKING:
    from .file_data import FileDataRead
    from .invoice import InvoiceRead
    UserRead.model_rebuild()
