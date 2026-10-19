from typing import Optional
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str
