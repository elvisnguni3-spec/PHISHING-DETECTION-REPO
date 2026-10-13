from app.database.connection import engine
from app.database.base import Base

# import models so SQLAlchemy "sees" them
from app.models.user import User
from app.models.scan_result import ScanResult

def create_tables():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
    print("Tables created successfully!")
