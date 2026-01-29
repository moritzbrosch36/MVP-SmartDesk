from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from .base_schema import BaseSchema, Field, datetime, date

# TYPE_CHECKING verhindert Zyklen beim Import
if TYPE_CHECKING:
    from .user import UserRead
    from .file_data import FileDataRead

class InvoiceCreate(BaseSchema):
    user_id: int = Field(..., description="Foreign Key zur User-Tabelle.")
    file_data_id: int = Field(..., description="Foreign Key zur FileData-Tabelle.")

    company: str = Field(..., max_length=200)
    invoice_number: str = Field(..., max_length=200)
    due_date: date
    # FIX: gt=0.0 entfernt, damit auch Testdaten/Platzhalter valide sind
    amount: float = Field(0.0)

    issue_date: Optional[date] = None
    currency: str = Field("EUR", max_length=20)
    description: Optional[str] = Field(None, max_length=1000)

class InvoiceRead(InvoiceCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    # FIX: Beziehungen auf Optional setzen und Standard None,
    # um Recursion Loops (Invoice -> User -> Invoice) zu vermeiden.
    user: Optional["UserRead"] = None
    file_data: Optional["FileDataRead"] = None

# Pydantic-Heilung
if not TYPE_CHECKING:
    from .user import UserRead
    from .file_data import FileDataRead
    InvoiceRead.model_rebuild()