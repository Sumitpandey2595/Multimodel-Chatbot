import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from backend.app.config import settings
from backend.app.database.base import Base
# Import models so Base has them registered
import backend.app.models

logger = logging.getLogger("uvicorn.error")

def get_engine():
    """
    Creates the SQLAlchemy engine.
    Tries PostgreSQL first as specified in DATABASE_URL.
    If PostgreSQL is unreachable, falls back to SQLite for effortless local development.
    """
    db_url = settings.DATABASE_URL
    try:
        if db_url.startswith("postgresql"):
            logger.info(f"Connecting to PostgreSQL database: {db_url.split('@')[-1]}")
            engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 2})
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to PostgreSQL.")
            return engine
        else:
            return create_engine(db_url, connect_args={"check_same_thread": False})
    except Exception as e:
        logger.warning(
            f"Could not connect to PostgreSQL ({e}). "
            f"Falling back to local SQLite at {settings.FALLBACK_SQLITE_URL} for development."
        )
        return create_engine(
            settings.FALLBACK_SQLITE_URL,
            connect_args={"check_same_thread": False}
        )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initializes database tables.
    If pgvector is supported, attempts to activate the vector extension.
    """
    try:
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
                    logger.info("PostgreSQL pgvector extension verified/enabled.")
                except Exception as ext_err:
                    logger.warning(f"pgvector extension not enabled ({ext_err}); using standard vector storage.")
    except Exception as e:
        logger.warning(f"Database pre-check notice: {e}")

    Base.metadata.create_all(bind=engine)
    logger.info("Database schema created successfully.")

def get_db():
    """FastAPI dependency for obtaining a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
