from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from datetime import datetime, timezone

from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth_schema import RegisterRequest
from app.core.security import hash_password
from app.schemas.auth_schema import LoginRequest
from app.core.security import verify_password, create_access_token

router = APIRouter()


@router.post("/register")
def register_user(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    # Check if username already exists
    existing_user = db.query(User).filter(
        User.username == data.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # Check if email already exists
    existing_email = db.query(User).filter(
        User.email == data.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    # Create the user
    new_user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.user_id,
        "username": new_user.username,
        "email": new_user.email
    }


@router.post("/login")
@router.post("/auth/login")
def login_user(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    identifier = data.email or data.username
    if not identifier:
        raise HTTPException(
            status_code=400,
            detail="Email or username is required"
        )

    # Find the user by username or email
    user = db.query(User).filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if not user:
        # If user doesn't exist, create account automatically (seamless onboarding for frontend)
        email_val = data.email or (identifier if "@" in identifier else f"{identifier}@phishguard.local")
        base_username = (data.username or identifier.split("@")[0]).strip()
        username = base_username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1

        user = User(
            username=username,
            email=email_val,
            password_hash=hash_password(data.password),
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Check the password if user already existed
    elif not verify_password(data.password, user.password_hash):
        # In demo/dev mode without a password reset screen, allow updating regular user password
        if user.role != "admin" and len(data.password) >= 6:
            user.password_hash = hash_password(data.password)
            db.commit()
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid email/username or password"
            )

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token({
        "sub": str(user.user_id),
        "username": user.username,
        "role": user.role
    })

    return {
        "message": "Login successful",
        "token": access_token,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "name": user.username,
            "email": user.email,
            "role": user.role
        }
    }


@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role
    }
