from source.db.db_blueprint import db
from sqlalchemy.inspection import inspect

# Hilfsfunktion: SQLAlchemy Object -> dict
def to_dict(instance):
    return {c.key: getattr(instance, c.key)
            for c in inspect(instance).mapper.column_attrs}


# ------------------------------------------
# CREATE
# ------------------------------------------
def crud_create(model, data: dict):
    obj = model(**data)
    db.session.add(obj)
    db.session.commit()
    return to_dict(obj)

# ------------------------------------------
# READ
# ------------------------------------------
def crud_read(model, filters: dict = None):
    query = model.query

    if filters:
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)

    return [to_dict(x) for x in query.all()]

# ------------------------------------------
# GET ONE
# ------------------------------------------
def crud_get_one(model, item_id):
    obj = model.query.get(item_id)
    if obj:
        return to_dict(obj)
    return None

# ------------------------------------------
# UPDATE
# ------------------------------------------
def crud_update(model, item_id, data: dict):
    obj = model.query.get(item_id)
    if not obj:
        return None

    for key, value in data.items():
        if hasattr(obj, key):
            setattr(obj, key, value)

    db.session.commit()
    return to_dict(obj)

# ------------------------------------------
# DELETE
# ------------------------------------------
def crud_delete(model, item_id):
    obj = model.query.get(item_id)
    if not obj:
        return False
    db.session.delete(obj)
    db.session.commit()
    return True