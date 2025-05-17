from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import logging
from app.config.config import getConfig # Import your getConfig

# Load environment variables (done by getConfig now)
# load_dotenv() # No longer needed here if getConfig handles it

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# Get the current configuration object
current_config = getConfig()
DATABASE_URL = current_config.SQLALCHEMY_DATABASE_URI # Use the URI from config

Base = declarative_base()

# Synchronous Engine
engine = create_engine(
    DATABASE_URL,
    echo=getattr(current_config, 'SQLALCHEMY_ECHO', False), # Optionally use SQLALCHEMY_ECHO from config
    poolclass=NullPool
)

# Synchronous Session Factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Dependency to get database session
def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()