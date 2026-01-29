import json
import os
import hashlib
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, desc, asc
from sqlalchemy.orm import relationship, clear_mappers

db = SQLAlchemy()

COLUMN_TYPES = {
    "Integer": Integer, "String": String, "Float": Float,
    "DateTime": DateTime, "Date": Date
}

def calculate_file_hash(file_path):
    """Berechnet SHA256 Hash einer Datei."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def parse_column(col_definition):
    parts = [p.strip() for p in col_definition.split(",")]
    type_part = parts[0]
    if "(" in type_part:
        type_name = type_part.split("(")[0]
        size = int(type_part.split("(")[1].replace(")", ""))
        column_type = COLUMN_TYPES[type_name](size)
    else:
        column_type = COLUMN_TYPES[type_part]()

    kwargs = {}
    for p in parts[1:]:
        if p.startswith("ForeignKey"):
            kwargs["ForeignKey"] = p
            continue
        if "=" not in p: continue
        key, val = p.split("=")
        key, val = key.strip(), val.strip()
        if val == "True": val = True
        elif val == "False": val = False
        elif val == "datetime.utcnow":
            kwargs["default"] = datetime.utcnow
            continue
        elif val.isdigit(): val = int(val)
        kwargs[key] = val
    return column_type, kwargs

def generate_models(schema_path):
    if db.metadata.tables: return MODEL_REGISTRY
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    models = {}
    for model_name, data in schema.items():
        attrs = {"__tablename__": data["tablename"], "__module__": __name__}
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
            attrs[rel_name] = relationship(rel_data["model"], backref=rel_data.get("backref"), lazy=True)
        models[model_name] = type(model_name, (db.Model,), attrs)
    return models

MODEL_REGISTRY = {}

def init_database(app):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
    db_folder = os.path.join(base_dir, "source", "db")
    if not os.path.exists(db_folder): os.makedirs(db_folder)
    db_path = os.path.join(db_folder, "smartdesk.db")
    schema_path = os.path.join(db_folder, "db_schema.json")
    db_already_exists = os.path.exists(db_path)

    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    global MODEL_REGISTRY
    MODEL_REGISTRY = generate_models(schema_path)

    with app.app_context():
        db.create_all()
        if db_already_exists:
            count = get_model("Invoice").query.count()
            print(f"[System] DB geladen: {count} Rechnungen vorhanden.")
        else:
            print(f"[System] DB neu erstellt: {db_path}")

def get_model(name: str):
    registry_lower = {k.lower(): v for k, v in MODEL_REGISTRY.items()}
    return registry_lower[name.lower()]

def is_hash_processed(file_hash: str):
    """Prüft Dubletten via Hash."""
    try:
        FileData = get_model("FileData")
        return db.session.query(FileData).filter(FileData.file_hash == file_hash).first() is not None
    except: return False

def execute_query_plan(query_plan):
    """Führt den vom LLM generierten Plan (mit Sorting/Limit) aus."""
    model_class = get_model(query_plan.main_table)
    query = db.session.query(model_class)
    # Filter, Sortierung & Limit hier anwenden (wie zuvor besprochen)
    # ... (Logik aus vorigem Schritt)
    return query.all()