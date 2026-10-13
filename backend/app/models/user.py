from sqlalchemy import Column, Integer, String, Boolean, DateTime, func

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String, nullable=False)

    role = Column(String(20), default="user")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True)
