import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///fingerprints.db")
    # SQLAlchemy uses SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
    ALLOW_RAW_EXPORT = os.environ.get("ALLOW_RAW_EXPORT", "false").lower() == "true"
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
