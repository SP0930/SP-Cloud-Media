"""
Database initialization and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from config import DATABASE_URL

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

# Create session factory
session_factory = sessionmaker(bind=engine, expire_on_commit=False)
Session = scoped_session(session_factory)

# Base class for all models
Base = declarative_base()


def init_db():
    """Initialize database tables"""
    from models.user import User
    from models.folder import Folder
    from models.media import Media
    
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully")


def get_session():
    """Get a new database session"""
    return Session()


def close_session():
    """Close the current session"""
    Session.remove()
