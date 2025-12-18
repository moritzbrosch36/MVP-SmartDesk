from source.models.base_schema import (BaseModel, Field, datetime,
                                       List, FileDataRead, InvoiceRead)
# Import der Basis_Elemente und forward References


# User
class UserCreate(BaseModel):
    name: str = Field(..., max_length=100) # dieses Feld ist erforderlich

class UserRead(UserCreate):
    id: int
    created_at: datetime

    # Verschachtelung der Beziehung (Nutzung der importierten String Referenzen)
    file: List[FileDataRead] = []
    invoices: List[InvoiceRead] = []

    class Config:
        from_attributes = True

# Wichtig: model_rebuild MUSS hier ausgeführt werden,
# da die Klasse UserRead in dieser Datei definiert wurde.
UserRead.model_rebuild()