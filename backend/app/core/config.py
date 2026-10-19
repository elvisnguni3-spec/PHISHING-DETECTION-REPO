import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./phishguard.db")
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "phishguard-development-secret-key-32bytes-min")
        self.JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
        self.DETECTION_ENGINE_URL = os.getenv("DETECTION_ENGINE_URL", "http://127.0.0.1:8001")


settings = Settings()
