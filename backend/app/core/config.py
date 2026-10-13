import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        self.JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))


settings = Settings()
