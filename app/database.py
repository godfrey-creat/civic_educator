# app/database.py
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

class DatabaseManager:
    def __init__(self, database_url=None, debug=None):
        self.database_url = database_url or settings.DATABASE_URL
        self.debug = debug if debug is not None else settings.DEBUG
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            echo=self.debug
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_db(self):
        """Database dependency"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

def get_db():
    """Database dependency"""
    db_manager = DatabaseManager()
    db = db_manager.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Provide a global Base for use in models
Base = declarative_base()

# Provide a global engine for use elsewhere in the app
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG
)