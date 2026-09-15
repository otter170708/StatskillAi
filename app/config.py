import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "StatSkill AI"
    ENV: str = "development"
    SECRET_KEY: str = "statskill-hackathon-2026-secret-key"
    DATABASE_URL: str = "sqlite:///./statskill.db"
    
    # AI Engine Configuration
    AI_PROVIDER: str = "mock"  # "mock", "gemini", "openai", "anthropic"
    AI_API_KEY: str = ""
    AI_MODEL_NAME: str = "gemini-2.5-flash"
    AI_BASE_URL: str = ""
    AI_MAX_TOKENS: int = 2048
    AI_TEMPERATURE: float = 0.2
    
    # Feature Flags & Limits
    ENABLE_OCR: bool = True
    ENABLE_HUMAN_REVIEW_MODE: bool = True
    MAX_UPLOAD_FILE_SIZE_MB: int = 15
    ALLOWED_FILE_TYPES: str = "application/pdf,text/plain,application/vnd.ms-powerpoint"
    LOG_LEVEL: str = "INFO"
    BACKEND_BASE_URL: str = "http://localhost:8000"
    
    # Defaults
    DEFAULT_NUM_QUESTIONS_PER_QUIZ: int = 5
    MIN_CONFIDENCE_FOR_CONFIRMED_GAP: float = 0.7
    MAX_RECOMMENDATIONS_PER_GAP: int = 2

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
