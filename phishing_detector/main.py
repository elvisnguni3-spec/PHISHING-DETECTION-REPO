from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Phishing Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DetectRequest(BaseModel):
    input: str
    input_type: Optional[str] = "auto"

class DetectBatchRequest(BaseModel):
    inputs: List[dict]
    parallel: Optional[bool] = True
    max_concurrent: Optional[int] = 5

from detectors.url_detector import URLDetector
from detectors.text_detector import TextDetector
from detectors.input_detector import InputTypeDetector

url_detector = URLDetector(api_key=os.getenv("URLSCAN_API_KEY"))
text_detector = TextDetector()
input_detector = InputTypeDetector()

@app.get("/")
async def root():
    return {"message": "Phishing Detection API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/detect")
async def detect_single(request: DetectRequest):
    print(f"POST /detect received: {request.input}")  # Debug
    
    if not request.input or not request.input.strip():
        raise HTTPException(status_code=400, detail="Input cannot be empty")
    
    input_type = request.input_type
    if input_type == "auto":
        input_type = input_detector.detect(request.input)
    
    print(f"Detected as: {input_type}")  # Debug
    
    try:
        if input_type == "URL":
            result = await url_detector.analyze(request.input)
        else:
            result = text_detector.analyze(request.input)
        
        return {
            "success": True,
            "data": result.to_dict()
        }
    except Exception as e:
        print(f"Error: {e}")  # Debug
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect/batch")
async def detect_batch(request: DetectBatchRequest):
    results = []
    for item in request.inputs:
        input_text = item.get("input", "")
        input_type = item.get("input_type", "auto")
        item_id = item.get("id", None)
        
        if not input_text or not input_text.strip():
            results.append({"id": item_id, "success": False, "error": "Empty input"})
            continue
        
        if input_type == "auto":
            input_type = input_detector.detect(input_text)
        
        try:
            if input_type == "URL":
                result = await url_detector.analyze(input_text)
            else:
                result = text_detector.analyze(input_text)
            
            results.append({"id": item_id, "success": True, "data": result.to_dict()})
        except Exception as e:
            results.append({"id": item_id, "success": False, "error": str(e)})
    
    return {"success": True, "total": len(results), "results": results}

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║     PHISHING & SCAM DETECTION API SERVER                            ║
    ║     Running on: http://localhost:8000                               ║
    ║     Press CTRL+C to stop                                            ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    # Show all registered routes
    print("Registered routes:")
    for route in app.routes:
        print(f"   {route.methods} {route.path}")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)