from flask import Blueprint, request, jsonify
from source.db.database import db
from source.services.crud import crud_create, crud_read, crud_update, crud_delete, crud_get_one

bp = Blueprint("crud_bp", __name__)

def get_models():
    """
    Liefert ein Dictionary aller dynamisch generierten Models.
    Key: Model-Name
    Value: Model-Klasse
    """
    models = {}

    for name, cls in db.Model._decl_class_registry.items():
        if name == '_sa_module_registry':
            continue
        models[name] = cls
    return models

# ------------------------------------------
# CREATE
# ------------------------------------------
@bp.route("/<model_name>", methods=["POST"])
def create(model_name):
    models = get_models()
    model = models.get(model_name)

    if not model:
        return jsonify({"error": "Unknown model"}), 404

    data = request.json
    obj = crud_create(model, data)
    return jsonify(obj), 201


# ------------------------------------------
# READ / GET ALL
# ------------------------------------------
@bp.route("/<model_name>", methods=["GET"])
def read(model_name):
    models = get_models()
    model = models.get(model_name)

    if not model:
        return jsonify({"error": "Unknown model"}), 404

    filters = request.args.to_dict()
    objs = crud_read(model, filters)
    return jsonify(objs)

# ------------------------------------------
# GET ONE
# ------------------------------------------
@bp.route("/<model_name>/<int:item_id>", methods=["GET"])
def get_one(model_name, item_id):
    models = get_models()
    model = models.get(model_name)

    if not model:
        return jsonify({"error": "Unknown model"}), 404

    obj = crud_get_one(model, item_id)
    if not obj:
        return jsonify({"error": "Not found"}), 404

    return jsonify(obj)

# ------------------------------------------
# UPDATE
# ------------------------------------------
@bp.route("/<model_name>/<int:item_id>", methods=["PUT"])
def update(model_name, item_id):
    models = get_models()
    model = models.get(model_name)

    if not model:
        return jsonify({"error": "Unknown model"}), 404

    data = request.json
    obj = crud_update(model, item_id, data)

    if not obj:
        return jsonify({"error": "Unknown model"}), 404

    return jsonify(obj)

# ------------------------------------------
# DELETE
# ------------------------------------------
@bp.route("/<model_name>/<int:item_id>", methods=["DELETE"])
def delete(model_name, item_id):
    models = get_models()
    model = models.get(model_name)

    if not model:
        return jsonify({"error": "Unknown model"}), 404

    success = crud_delete(model, item_id)
    return jsonify({"deleted": success})
