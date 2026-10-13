from passlib.context import CryptContext
from jose import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.database.connection import get_db
from app.models.user import User

from app.core.config import settings

security = HTTPBearer()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )


def decode_access_token(token: str):
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
    except Exception:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.user_id == int(user_id)).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user
