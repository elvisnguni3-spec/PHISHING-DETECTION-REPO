import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.scan_routes import router as scan_router
from app.routes.auth_routes import router as auth_router
from app.database.init_db import create_tables

# Create the database tables on startup (safe to run every time)
create_tables()

app = FastAPI(
     title="Phishing Detection System API",
     version="1.0.0"
)

# Extra allowed frontend addresses, comma separated, e.g. https://my-app.vercel.app
extra_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        *extra_origins,
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Phishing Detection API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(scan_router)
app.include_router(auth_router)
