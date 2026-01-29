from __future__ import annotations
from typing import List, TYPE_CHECKING, Optional
from .base_schema import BaseSchema, Field, datetime

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

    # Wir kappen auch hier die tiefen Listen-Beziehungen für die Standardansicht.
    # Falls du sie brauchst, nutze spezialisierte 'WithRelations' Modelle.
    # invoices: List["InvoiceRead"] = []

    # Der User kann als einfache Referenz bleiben (optional)
    user: Optional["UserRead"] = None


# --- Pydantic "Heilung" ---
if not TYPE_CHECKING:
    from .invoice import InvoiceRead
    from .user import UserRead

    FileDataRead.model_rebuild()