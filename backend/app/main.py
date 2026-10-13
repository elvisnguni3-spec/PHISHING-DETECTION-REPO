from fastapi import FastAPI
from app.routes.scan_routes import router as scan_router
from app.routes.auth_routes import router as auth_router

app = FastAPI(
     title="Phishing Detection System API",
     version="1.0.0"
)

@app.get("/")
def home():
    return {"message": "Phishing Detection API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(scan_router)
app.include_router(auth_router)
