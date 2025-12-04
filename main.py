import os
from flask import Flask
from models.db_blueprint import db, generate_models

def create_app():
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = \
        f"sqlite:///{os.path.join(basedir, 'database/smartdesk.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        generate_models() # Models erzeugen
        db.create_all()   # Tabellen automatisch erstellen

    return app

if __name__ == "__main__":
    create_app()
