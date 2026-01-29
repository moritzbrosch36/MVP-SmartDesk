from __future__ import annotations
from typing import List, TYPE_CHECKING, Optional
from .base_schema import BaseSchema, Field, datetime

# TYPE_CHECKING verhindert Import-Zyklen zur Laufzeit
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

    # WICHTIG: Wir lassen die Listen für Beziehungen hier weg oder
    # setzen sie auf Optional, um Recursion Loops zu vermeiden.
    # Für die KI-Antworten reicht meistens das User-Objekt selbst.
    # file: List["FileDataRead"] = []
    # invoices: List["InvoiceRead"] = []

# --- Pydantic "Heilung" ---
if not TYPE_CHECKING:
    from .file_data import FileDataRead
    from .invoice import InvoiceRead
    UserRead.model_rebuild()