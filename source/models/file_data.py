from __future__ import annotations
from typing import List, TYPE_CHECKING
from .base_schema import BaseSchema, Field, datetime

# 1. TYPE_CHECKING: Verhindert Import-Zyklen zur Laufzeit,
# ermöglicht der IDE (VS Code/PyCharm) aber trotzdem Autocomplete.
if TYPE_CHECKING:
    from .invoice import InvoiceRead
    from .user import UserRead

# --- Schemas für die Erstellung ---
class FileDataCreate(BaseSchema):
    user_id: int = Field(..., description="Foreign Key zur User-Tabelle.")
    filename: str = Field(..., max_length=255)
    file_path: str = Field(..., max_length=500)
    file_type: str = Field(..., max_length=200)

# --- Schemas für das Auslesen ---
class FileDataRead(FileDataCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    # WICHTIG: Nutze Anführungszeichen für Klassen aus anderen Dateien.
    # Das sagt Pydantic: "Die Definition von InvoiceRead kommt später."
    invoices: List["InvoiceRead"] = []
    user: "UserRead"

# --- Pydantic "Heilung" ---
# Dieser Block wird erst ausgeführt, wenn Python die Datei komplett gelesen hat.
# model_rebuild() verknüpft dann die Strings "InvoiceRead" mit den echten Klassen.
if not TYPE_CHECKING:
    from .invoice import InvoiceRead
    from .user import UserRead
    FileDataRead.model_rebuild()
