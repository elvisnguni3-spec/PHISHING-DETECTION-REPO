from typing import Tuple, List

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("transformers not installed. Run: pip install transformers torch")


class TextAI:
    """AI model for text scam detection"""
    
    def __init__(self):
        self.model = None
        if TRANSFORMERS_AVAILABLE:
            try:
                self.model = pipeline(
                    "text-classification",
                    model="mrm8488/bert-tiny-finetuned-sms-spam-detection"
                )
                print("Text AI model loaded")
            except Exception as e:
                print(f"Failed to load AI model: {e}")
    
    def analyze(self, text: str) -> Tuple[float, List[str]]:
        """Returns (score 0-100, reasons list)"""
        reasons = []
        
        if not self.model:
            return 0, ["AI model not loaded - AI check skipped"]
        
        try:
            result = self.model(text[:512])[0]
            label = result['label']
            confidence = result['score']
            
            if label in ['SPAM', 'LABEL_1', 'scam']:
                score = confidence * 100
                reasons.append(f"AI detected scam content ({score:.0f}% confidence)")
            else:
                score = (1 - confidence) * 100
                reasons.append(f"AI found content legitimate ({score:.0f}% confidence)")
            
            return score, reasons
        except Exception as e:
            return 0, [f"AI check skipped: {str(e)[:50]}"]