import os
from datetime import timedelta
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Core App Settings
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/tmp/uploads") # This might be superseded by TEMP_DIR logic
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max upload

    # SQLAlchemy Settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Common Flask-SQLAlchemy setting, might not be used by raw SQLAlchemy
    POSTGRES_HOST = os.environ.get("POSTGRES_SERVER", "localhost") # Renamed from POSTGRES_SERVER
    POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432)) # Ensure it's an int
    POSTGRES_USER = os.environ.get("POSTGRES_USER", "user")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "password")
    POSTGRES_DB = os.environ.get("POSTGRES_DB", "app_db")

    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # MinIO configuration
    MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000") # Adjusted default for Docker
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "anhyeuem")
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "anhyeuem")
    MINIO_BUCKET_NAME = os.environ.get("MINIO_BUCKET_NAME", "documents")
    
    # RabbitMQ configuration (as in your original file)
    RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", 5672))
    RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "rag")
    RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "rag")
    RABBITMQ_VHOST = os.environ.get("RABBITMQ_VHOST", "/")
    RABBITMQ_DOCUMENT_QUEUE = os.environ.get("RABBITMQ_DOCUMENT_QUEUE", "document_processing")
    RABBITMQ_CHUNK_QUEUE = os.environ.get("RABBITMQ_CHUNK_QUEUE", "document_chunking")

    # --- Qdrant Configuration ---
    QDRANT_HOST: str = os.environ.get("QDRANT_HOST", "localhost")
    QDRANT_PORT: str = os.environ.get("QDRANT_PORT", 6334) # gRPC port for client
    QDRANT_API_KEY: str | None = os.environ.get("QDRANT_API_KEY", None) # Optional API key
    QDRANT_COLLECTION_NAME: str = os.environ.get("QDRANT_COLLECTION_NAME", "document_chunks")
    
    # --- Embedding Model Configuration ---
    EMBEDDING_MODEL_NAME: str = os.environ.get("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    # Dimension for all-MiniLM-L6-v2 is 384. If you change model, update this.
    EMBEDDING_DIMENSION: int = int(os.environ.get("EMBEDDING_DIMENSION", 384))

        # --- LLM Chat Provider Configuration ---
    CHAT_PROVIDER: str = os.environ.get("CHAT_PROVIDER", "gemini").lower() 

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

    # Gemini Configuration (via OpenAI compatible API)
    GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-pro") # Example model
    # For Google AI Studio, base_url is often specific per model type
    GEMINI_API_BASE_URL: str = os.environ.get("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")


    # Ollama Configuration (reusing existing where possible)
    OLLAMA_API_BASE: str = os.environ.get("OLLAMA_API_BASE", "http://127.0.0.1:11434")
    OLLAMA_CHAT_MODEL: str = os.environ.get("OLLAMA_CHAT_MODEL", os.environ.get("OLLAMA_MODEL", "llama3.2:latest"))
    
    # Default LLM settings
    LLM_DEFAULT_TEMPERATURE: float = float(os.environ.get("LLM_DEFAULT_TEMPERATURE", 0.7))
    LLM_DEFAULT_MAX_TOKENS: int = int(os.environ.get("LLM_DEFAULT_MAX_TOKENS", 1500))
    LLM_INPUT_CHUNK_MAX_WORDS: int = int(os.environ.get("LLM_INPUT_CHUNK_MAX_WORDS", 2000)) # Maximum words per chunk for LLM input processing.

class DevelopmentConfig(Config):
    DEBUG = True
    # SQLALCHEMY_ECHO = True # Useful for debugging SQL queries


class TestingConfig(Config):
    TESTING = True
    # Example: Use a separate test database
    # POSTGRES_DB = os.environ.get("TEST_POSTGRES_DB", "app_test_db")
    # SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{POSTGRES_DB}"
    # QDRANT_COLLECTION_NAME = os.environ.get("QDRANT_TEST_COLLECTION_NAME", "test_document_chunks")


class ProductionConfig(Config):
    DEBUG = False
    # Add any production-specific settings here
    # For example, more robust logging, different external service URLs, etc.

    
# Dictionary to map environment names to configuration classes
_config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig, # Default to development if ENV is not set or invalid
}

_current_config = None

def getConfig(env: str | None = None) -> Config: # Added type hint for clarity
    """
    Retrieves the configuration object for the specified environment.
    If no environment is specified, it uses the value of the 'ENV'
    environment variable, defaulting to 'development'.
    Caches the loaded configuration object.
    """
    global _current_config
    if _current_config is None:
        if env is None:
            env = os.getenv("ENV", "development").lower() # Ensure lowercase for matching
        
        config_class = _config_map.get(env)
        if not config_class:
            print(f"Warning: Environment '{env}' not found in config map. Using default ({_config_map['default'].__name__}).")
            config_class = _config_map["default"]
        
        _current_config = config_class()
        print(f"Loading configuration for environment: {env} ({_current_config.__class__.__name__})")
    return _current_config

# To use in your application:
# from app.config.config import getConfig
# current_app_config = getConfig()
# db_uri = current_app_config.SQLALCHEMY_DATABASE_URI
# qdrant_host = current_app_config.QDRANT_HOST
