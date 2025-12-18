from source.models.base_schema import (BaseModel, Field, datetime,
                                       date, Optional, UserRead, FileDataRead)
# Import der Basis-Elemente und forward References


# Invoice
class InvoiceCreate(BaseModel):
    # Foreign Keys (muss beim Erstellen bereitgestellt werden)
    user_id: int = Field(..., description="Foreign Key zur User-Tabelle.")
    file_data_id: int = Field(..., description="Foreign Key zur FileData-Tabelle.")

    # Pflichtfelder
    company: str = Field(..., max_length=200)
    invoice_number: str = Field(..., max_length=200)
    due_date: date
    amount: float = Field(..., gt=0.0)

    # Optionale Felder/ Default-Werte
    issue_date: Optional[date] = None # Im DB: DateTime, kann Null sein
    currency: str = Field("EUR", max_length=20) # Im DB: Default 'EUR'
    description: Optional[str] = Field(None, max_length=1000) # Kann Null sein

class InvoiceRead(InvoiceCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    # Verschachtelte Objekte (ersetzen die einfachen IDs für die Ausgabe)
    user: UserRead
    file_data: FileDataRead

    class Config:
        from_attributes = True

# Wichtig: model_rebuild MUSS hier ausgeführt werden
InvoiceRead.model_rebuild()