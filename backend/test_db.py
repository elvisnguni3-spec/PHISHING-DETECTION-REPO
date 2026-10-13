from sqlalchemy import text
from app.database.connection import SessionLocal


def test_db_connection():
    try:
        db = SessionLocal()

        result = db.execute(text("SELECT 1"))
        print("Database connection successful:", result.fetchone())

        db.close()

    except Exception as e:
        print("Database connection failed:")
        print(e)


if __name__ == "__main__":
    test_db_connection()
