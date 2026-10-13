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
def login_user(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    # Find the user
    user = db.query(User).filter(
        User.username == data.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Check the password
    if not verify_password(data.password, user.password_hash):
       raise HTTPException(
                  status_code=401,
                  detail="Invalid username or password"
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
            "access_token": access_token,
            "token_type": "bearer"
        }


@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role
    }
