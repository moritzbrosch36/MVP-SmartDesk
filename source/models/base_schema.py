from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date # noqa: F401
from typing import Optional, List, Literal # noqa: F401

class BaseSchema(BaseModel):
    """
    Diese Basis-Klasse dient als Eltern-Klasse für alle deine Models.
    Hier kommen Einstellungen rein, die für alle gelten sollen.
    """
    # In Pydantic V2 nutzt man ConfigDict statt der alten class Config
    model_config = ConfigDict(from_attributes=True)

# Hier kannst du Hilfsfunktionen oder globale Typen definieren,
# die ÜBERALL gebraucht werden, aber keine anderen Models importieren.