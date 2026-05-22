import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./appointments.db")
    
    # Performance
    LATENCY_TARGET_MS = int(os.getenv("LATENCY_TARGET_MS", 450))
    
    # Session
    SESSION_TTL_SECONDS = 1800  # 30 minutes
    
    # App Settings
    APP_NAME = "Voice AI Healthcare Agent"
    APP_VERSION = "1.0.0"

config = Config()