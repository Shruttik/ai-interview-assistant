from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.app.config import settings

# Setup engine connection.
# check_same_thread is only required for SQLite.
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

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
