import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.app.config import settings

# Setup engine connection.
# check_same_thread is only required for SQLite.
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Safely create parent directories for SQLite database if they don't exist
    db_path = settings.database_url.split("sqlite:///")[-1]
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create database directory {db_dir}: {e}")

engine = create_engine(
    settings.database_url, 
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

Base = declarative_base()

def get_db():
    """
    FastAPI dependency yielding a database session.
    Automatically closes the connection when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
