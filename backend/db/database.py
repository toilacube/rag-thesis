from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv
from app.config.config import getConfig

# Load environment variables
load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://rag:rag@localhost:5432/ragdb")

# SQLAlchemy Base Model
Base = declarative_base()

# Synchronous Engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Log SQL queries
    poolclass=NullPool  # Disable connection pooling
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
