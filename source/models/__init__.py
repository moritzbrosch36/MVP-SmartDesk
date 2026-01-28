# source/models/__init__.py

# Ich importiere hier NUR die Pydantic-Schemas (die statischen Dateien)
from .user import UserRead, UserCreate
from .file_data import FileDataRead, FileDataCreate
from .invoice import InvoiceRead, InvoiceCreate

# Export für den einfachen Zugriff
__all__ = [
    "UserRead", "UserCreate",
    "FileDataRead", "FileDataCreate",
    "InvoiceRead", "InvoiceCreate"
]