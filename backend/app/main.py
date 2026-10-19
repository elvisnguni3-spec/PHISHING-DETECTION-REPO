from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.scan_routes import router as scan_router
from app.routes.auth_routes import router as auth_router

app = FastAPI(
     title="Phishing Detection System API",
     version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
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

