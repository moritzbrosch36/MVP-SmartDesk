from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from .base_schema import BaseSchema, Field, datetime, date

# 1. TYPE_CHECKING: Verhindert Import-Zyklen (Invoice -> User -> Invoice)
if TYPE_CHECKING:
    from .user import UserRead
    from .file_data import FileDataRead

# --- Schemas für die Erstellung ---
class InvoiceCreate(BaseSchema):
    # Foreign Keys
    user_id: int = Field(..., description="Foreign Key zur User-Tabelle.")
    file_data_id: int = Field(..., description="Foreign Key zur FileData-Tabelle.")

    # Pflichtfelder
    company: str = Field(..., max_length=200)
    invoice_number: str = Field(..., max_length=200)
    due_date: date
    amount: float = Field(..., gt=0.0)

    # Optionale Felder
    issue_date: Optional[date] = None
    currency: str = Field("EUR", max_length=20)
    description: Optional[str] = Field(None, max_length=1000)

# --- Schemas für das Auslesen ---
class InvoiceRead(InvoiceCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    # 2. Nutze Strings für die Typen, um ForwardReference-Fehler zu vermeiden
    user: "UserRead"
    file_data: "FileDataRead"

# --- Pydantic "Heilung" ---
# Erst hier werden die Klassen UserRead und FileDataRead wirklich importiert,
# damit Pydantic die oben genutzten Strings auflösen kann.
if not TYPE_CHECKING:
    from .user import UserRead
    from .file_data import FileDataRead
    InvoiceRead.model_rebuild()
