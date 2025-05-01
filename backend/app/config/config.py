import os
from datetime import timedelta

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Load environment variables from .env file

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/tmp/uploads")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max upload

    POSTGRES_HOST = os.environ.get("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT", 5432)
    POSTGRES_USER = os.environ.get("POSTGRES_USER", "user")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "password")
    POSTGRES_DB = os.environ.get("POSTGRES_DB", "app_db")

    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # MinIO configuration
    MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "anhyeuem")
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "anhyeuem")
    MINIO_BUCKET_NAME = os.environ.get("MINIO_BUCKET_NAME", "documents")
    
    # RabbitMQ configuration
    RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", 5672))
    RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "rag")
    RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "rag")
    RABBITMQ_VHOST = os.environ.get("RABBITMQ_VHOST", "/")
    RABBITMQ_DOCUMENT_QUEUE = os.environ.get("RABBITMQ_DOCUMENT_QUEUE", "document_processing")
    RABBITMQ_CHUNK_QUEUE = os.environ.get("RABBITMQ_CHUNK_QUEUE", "document_chunking")

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    
class ProductionConfig(Config):
    pass
    
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

def getConfig(env=None):
    if env is None:
        env = os.getenv("ENV", "development")
    return config.get(env, DevelopmentConfig)