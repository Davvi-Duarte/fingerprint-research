from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from .config import Config
from .database import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    Migrate(app, db)

    CORS(app, origins=app.config["CORS_ORIGINS"])

    from .routes import bp
    app.register_blueprint(bp)

    return app
