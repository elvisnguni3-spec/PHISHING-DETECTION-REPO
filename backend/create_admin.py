from getpass import getpass

from app.database.connection import SessionLocal
from app.models.user import User

from app.core.security import hash_password

def create_admin():
    db = SessionLocal()
    try:
        username = input("Admin username: ").strip()
        email = input("Admin email: ").strip()
        password = getpass("Admin password: ")
        confirm_password = getpass("Confirm admin password: ")

        if not username or not email or not password:
            print("Error: All fields are required.")
            return

        if password != confirm_password:
            print("Error: Passwords do not match.")
            return

        if len(password) < 12:
            print("Error: Use a password with at least 12 characters.")
            return

        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            print("Error: That username or email is already registered.")
            return


        admin = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"Admin account created successfully. User ID: {admin.user_id}")

    except Exception:
        db.rollback()
        print("Admin creation failed. Check your database connection and try again.")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
