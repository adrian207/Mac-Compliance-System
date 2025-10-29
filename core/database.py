"""
Database Connection and ORM Module

Author: Adrian Johnson <adrian207@gmail.com>

Manages database connections and provides base models for ORM operations.
"""

from contextlib import contextmanager
from datetime import datetime
from typing import Generator

from sqlalchemy import Column, DateTime, Integer, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from core.config import get_config
from core.logging_config import get_logger

logger = get_logger(__name__)

# Base class for all ORM models
Base = declarative_base()


class BaseModel(Base):
    """Base model class with common fields."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DatabaseManager:
    """
    Database connection manager.
    
    Provides connection pooling and session management for database operations.
    """
    
    def __init__(self):
        """Initialize database manager."""
        self.config = get_config()
        self.engine = None
        self.SessionLocal = None
    
    def initialize(self) -> None:
        """
        Initialize database engine and session factory.
        
        Raises:
            Exception: If database configuration is missing or connection fails
        """
        if not self.config.database:
            raise Exception("Database configuration not found")
        
        db_config = self.config.database
        
        # Create engine with connection pooling
        self.engine = create_engine(
            db_config.connection_string,
            pool_size=db_config.pool_size,
            max_overflow=db_config.max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            echo=self.config.log_level == "DEBUG"
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(
            "database_initialized",
            host=db_config.host,
            database=db_config.database
        )
    
    def create_tables(self) -> None:
        """
        Create all database tables defined by ORM models.
        
        [Unverified] This creates tables based on the current model definitions.
        Existing tables will not be altered.
        """
        if not self.engine:
            raise Exception("Database not initialized. Call initialize() first.")
        
        Base.metadata.create_all(bind=self.engine)
        logger.info("database_tables_created")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session context manager.
        
        Usage:
            with db_manager.get_session() as session:
                # Perform database operations
                session.query(Model).all()
        
        Yields:
            Session: SQLAlchemy session object
        
        Raises:
            Exception: If database is not initialized
        """
        if not self.SessionLocal:
            raise Exception("Database not initialized. Call initialize() first.")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("database_session_error", error=str(e))
            raise
        finally:
            session.close()
    
    def close(self) -> None:
        """Close database connections and dispose of connection pool."""
        if self.engine:
            self.engine.dispose()
            logger.info("database_closed")


# Global database manager instance
_db_manager: DatabaseManager = None


def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Returns:
        DatabaseManager: Global database manager
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize()
    return _db_manager


def get_db_session() -> Generator[Session, None, None]:
    """
    Get a database session for dependency injection.
    
    Usage with FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db_session)):
            return db.query(Item).all()
    
    Yields:
        Session: SQLAlchemy session object
    """
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        yield session

