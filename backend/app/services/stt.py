import time
import base64
import tempfile
import os
from typing import Dict, Any

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available, using mock STT")

class STTService:
    """Speech-to-Text service using OpenAI Whisper"""
    
    def __init__(self, api_key: str = None):
        if OPENAI_AVAILABLE and api_key:
            openai.api_key = api_key
        self.api_key = api_key
    
    async def transcribe(self, audio_base64: str) -> Dict[str, Any]:
        """
        Convert audio to text
        Returns: {"text": str, "latency_ms": float}
        """
        start_time = time.time()
        
        if not audio_base64:
            return {"text": "", "latency_ms": 0, "error": "No audio provided"}
        
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_base64)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name
            
            if OPENAI_AVAILABLE and self.api_key:
                # Use OpenAI Whisper API
                with open(tmp_path, "rb") as audio_file:
                    response = openai.Audio.transcribe(
                        model="whisper-1",
                        file=audio_file
                    )
                text = response.get("text", "")
            else:
                # Mock for development
                text = "Book appointment with cardiologist tomorrow"
            
            # Cleanup
            os.unlink(tmp_path)
            
            latency = (time.time() - start_time) * 1000
            
            return {
                "text": text,
                "latency_ms": round(latency, 2)
            }
            
        except Exception as e:
            return {
                "text": "",
                "latency_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }