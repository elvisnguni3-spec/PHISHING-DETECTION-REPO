from typing import Tuple, List

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class URLAI:
    """AI model for URL phishing detection"""
    
    def __init__(self):
        self.model = None
        if TRANSFORMERS_AVAILABLE:
            try:
                # Using a model that can analyze URLs (falls back to text analysis)
                self.model = pipeline(
                    "text-classification",
                    model="mrm8488/bert-tiny-finetuned-sms-spam-detection"
                )
                print("URL AI model loaded")
            except Exception as e:
                print(f"Failed to load URL AI model: {e}")
    
    def analyze(self, url: str) -> Tuple[float, List[str]]:
        """Returns (score 0-100, reasons list)"""
        reasons = []
        
        if not self.model:
            return 0, ["AI model not loaded - AI check skipped"]
        
        try:
            # Clean URL for analysis
            clean_url = url.replace('http://', '').replace('https://', '').replace('www.', '')
            result = self.model(clean_url[:512])[0]
            label = result['label']
            confidence = result['score']
            
            if label in ['SPAM', 'LABEL_1']:
                score = confidence * 100
                reasons.append(f"AI found suspicious patterns ({score:.0f}% confidence)")
            else:
                score = (1 - confidence) * 100
                reasons.append(f"AI found normal patterns ({score:.0f}% confidence)")
            
            return score, reasons
        except Exception as e:
            return 0, [f"AI check skipped: {str(e)[:50]}"]