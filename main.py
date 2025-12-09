import os.path

from flask import Flask
from source.api.routes import bp
from source.db.database import init_database

app = Flask(__name__)

# DB konfigurieren
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = \
    f"sqlite:///{os.path.join(basedir, 'source/db/smartdesk.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# DB initialisieren + Models generieren
init_database(app)

# Blueprint registrieren
app.register_blueprint(bp)


if __name__ == "__main__":
    app.run(debug=True)
