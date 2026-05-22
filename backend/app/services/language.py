import time
from typing import Dict, Any

try:
    from langdetect import detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    print("⚠️ langdetect not available, using fallback detection")

class LanguageService:
    """Multilingual language detection service"""
    
    LANGUAGE_MAP = {
        'en': 'english',
        'hi': 'hindi',
        'ta': 'tamil',
        'mr': 'hindi',  # Marathi -> Hindi
        'bn': 'hindi',  # Bengali -> Hindi
        'te': 'tamil',  # Telugu -> Tamil
        'kn': 'tamil',  # Kannada -> Tamil
    }
    
    # Hindi Unicode range: 0900-097F
    HINDI_RANGE = range(0x0900, 0x0980)
    # Tamil Unicode range: 0B80-0BFF
    TAMIL_RANGE = range(0x0B80, 0x0C00)
    
    async def detect(self, text: str) -> Dict[str, Any]:
        """
        Detect language from text
        Returns: {"language": "english/hindi/tamil", "latency_ms": float}
        """
        start_time = time.time()
        
        if not text or not text.strip():
            return {"language": "english", "latency_ms": 0.0}
        
        try:
            if LANGDETECT_AVAILABLE:
                detected_code = detect(text)
                language = self.LANGUAGE_MAP.get(detected_code, 'english')
            else:
                # Fallback: Check Unicode ranges
                if any(ord(c) in self.HINDI_RANGE for c in text):
                    language = 'hindi'
                elif any(ord(c) in self.TAMIL_RANGE for c in text):
                    language = 'tamil'
                else:
                    language = 'english'
        except Exception:
            language = 'english'
        
        latency = (time.time() - start_time) * 1000
        
        return {
            "language": language,
            "latency_ms": round(latency, 2)
        }