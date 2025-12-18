# Pydantic
from pydantic import BaseModel, Field

from datetime import datetime, date

from typing import Optional, List, TYPE_CHECKING, Literal


#WICHTIG: Hier werden die Importe an die neuen Dateinamen angepasst:
if TYPE_CHECKING:
    from source.models.invoice import InvoiceRead
    from source.models.file_data import FileDataRead
    from source.models.user import UserRead
else:
    InvoiceRead = "InvoiceRead"
    FileDataRead = "FileDataRead"
    UserRead = "UserRead"
