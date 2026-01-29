import json
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import clear_mappers

db = SQLAlchemy()

# Zuordnung zwischen String Namen und SQLAlchemy Python Objekten
# 'Date' wurde hinzugefügt für reine Datumsfelder ohne Uhrzeit
COLUMN_TYPES = {
    "Integer": Integer,
    "String": String,
    "Float": Float,
    "DateTime": DateTime,
    "Date": Date
}


def parse_column(col_definition):
    """
    Konvertiert einen String aus der db_schema.json in SQLAlchemy Spaltenargumente.
    """
    parts = [p.strip() for p in col_definition.split(",")]

    # --- Type Handling ---
    type_part = parts[0]
    if "(" in type_part:
        type_name = type_part.split("(")[0]
        size = int(type_part.split("(")[1].replace(")", ""))
        column_type = COLUMN_TYPES[type_name](size)
    else:
        if type_part not in COLUMN_TYPES:
            raise ValueError(f"Unbekannter Typ: {type_part}")
        column_type = COLUMN_TYPES[type_part]()

    # --- Keyword arguments ---
    kwargs = {}
    for p in parts[1:]:
        if p.startswith("ForeignKey"):
            kwargs["ForeignKey"] = p
            continue
        if "=" not in p:
            continue

        key, val = p.split("=")
        key, val = key.strip(), val.strip()

        if val == "True":
            val = True
        elif val == "False":
            val = False
        elif val == "datetime.utcnow":
            # Wir speichern die Referenz auf die Funktion
            kwargs["default"] = datetime.utcnow
            continue
        elif val.isdigit():
            val = int(val)
        kwargs[key] = val

    return column_type, kwargs


# --------------------------------------------------------
#               2 - Phasen Modell-Generator
# --------------------------------------------------------

def generate_models(schema_path):
    """Baut SQLAlchemy Klassen basierend auf der JSON-Datei."""
    try:
        clear_mappers()
    except Exception:
        pass
    db.metadata.clear()

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    models = {}
    for model_name, data in schema.items():
        attrs = {
            "__tablename__": data["tablename"],
            "__module__": __name__,
        }

        for col_name, definition in data.get("columns", {}).items():
            column_type, kwargs = parse_column(definition)
            if "ForeignKey" in kwargs:
                fk_raw = kwargs.pop("ForeignKey")
                fk_target = fk_raw[fk_raw.index("(") + 1: fk_raw.rindex(")")].strip("'\" ")
                col = Column(column_type, ForeignKey(fk_target), **kwargs)
            else:
                col = Column(column_type, **kwargs)
            attrs[col_name] = col

        for rel_name, rel_data in data.get("relationships", {}).items():
            attrs[rel_name] = relationship(
                rel_data["model"],
                backref=rel_data.get("backref"),
                lazy=True
            )

        models[model_name] = type(model_name, (db.Model,), attrs)
    return models


# --------------------------------------------------------
#               INIT & REGISTRY
# --------------------------------------------------------
MODEL_REGISTRY = {}


def init_database(app):
    """Initialisiert die DB im Ordner source/db/."""
    # 1. Ermittle Pfad: database.py (services) -> source -> Demo (Root)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))

    # 2. Zielordner definieren: Demo/source/db/
    db_folder = os.path.join(base_dir, "source", "db")

    # Ordner erstellen, falls er fehlt
    if not os.path.exists(db_folder):
        os.makedirs(db_folder)

    db_path = os.path.join(db_folder, "smartdesk.db")
    schema_path = os.path.join(db_folder, "db_schema.json")

    # 3. SQLAlchemy Konfiguration
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # 4. Modelle generieren
    global MODEL_REGISTRY
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema-Datei fehlt in: {schema_path}")

    MODEL_REGISTRY = generate_models(schema_path)

    with app.app_context():
        db.create_all()
        print(f"[System] Datenbank bereit unter: {db_path}")
        print(f"[System] Schema geladen von: {schema_path}")


def get_model(name: str):
    """Sucht ein Modell case-insensitive in der Registry."""
    registry_lower = {k.lower(): v for k, v in MODEL_REGISTRY.items()}
    if name.lower() not in registry_lower:
        raise ValueError(f"Unknown model: {name}. Verfügbar: {list(MODEL_REGISTRY.keys())}")
    return registry_lower[name.lower()]
