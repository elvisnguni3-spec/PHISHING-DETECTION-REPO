from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


# Database URL from .env
DATABASE_URL = settings.DATABASE_URL

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
