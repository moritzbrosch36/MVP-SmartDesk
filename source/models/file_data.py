from source.models.base_schema import (BaseModel, Field, datetime,
                                       List, InvoiceRead, UserRead)
# Import der Basis-Elemente und forward References


# FileData
class FileDataCreate(BaseModel):
    user_id: int = Field(..., description="Foreign Key zur User-Tabelle.")
    filename: str = Field(..., max_length=255)
    file_path: str = Field(..., max_length=500)
    file_type: str = Field(..., max_length=200)

class FileDataRead(FileDataCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    # Beziehungen:
    invoices: List[InvoiceRead] = []
    user: UserRead

    class Config:
        from_attributes = True

# WICHTIG: model_rebuild MUSS hier ausgeführt werden
FileDataRead.model_rebuild()