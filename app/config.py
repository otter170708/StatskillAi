"""
StatSkill AI Configuration Module

This module loads and validates environment variables using pydantic-settings.
It provides centralized configuration management with type checking and validation.

Configuration can be loaded from:
1. Environment variables
2. .env file (using python-decouple or pydantic)
3. Default values defined here

Security:
- Sensitive values (API keys, database passwords) are NOT logged
- Missing required variables raise ConfigurationError on startup
- .env file is excluded from git via .gitignore
"""

import os
import logging
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ValidationError

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings and configuration.
    
    All environment variables are validated on instantiation.
    Required variables raise ValidationError if not provided.
    """
    
    # ======================================================================
    # APPLICATION CORE SETTINGS
    # ======================================================================
    
    APP_NAME: str = Field(
        default="StatSkill AI",
        description="Application name displayed in logs and API docs"
    )
    
    ENV: str = Field(
        default="development",
        description="Environment: 'development', 'staging', or 'production'"
    )
    
    SECRET_KEY: str = Field(
        default="statskill-hackathon-2026-secret-key",
        description="Secret key for cryptographic operations"
    )
    
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode (detailed errors, auto-reload)"
    )
    
    # ======================================================================
    # DATABASE CONFIGURATION
    # ======================================================================
    
    DATABASE_URL: str = Field(
        default="sqlite:///./statskill.db",
        description="Database connection URL (SQLite, PostgreSQL, MySQL, etc.)"
    )
    
    DB_POOL_SIZE: int = Field(
        default=20,
        description="Minimum number of database connections to maintain"
    )
    
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        description="Maximum number of overflow connections"
    )
    
    DB_POOL_TIMEOUT: int = Field(
        default=30,
        description="Timeout for connection acquisition (seconds)"
    )
    
    DB_POOL_RECYCLE: int = Field(
        default=3600,
        description="Seconds before connections are recycled"
    )
    
    DB_ECHO: bool = Field(
        default=False,
        description="Log all SQL statements (disable in production)"
    )
    
    # ======================================================================
    # AI PROVIDER CONFIGURATION
    # ======================================================================
    
    AI_PROVIDER: str = Field(
        default="mock",
        description="AI Provider: 'mock', 'gemini', 'openai', 'anthropic'"
    )
    
    AI_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for selected AI provider"
    )
    
    AI_MODEL_NAME: str = Field(
        default="gemini-flash-latest",
        description="Model name/identifier for the AI provider"
    )
    
    AI_BASE_URL: Optional[str] = Field(
        default=None,
        description="Custom base URL for AI provider (optional)"
    )
    
    AI_MAX_TOKENS: int = Field(
        default=2048,
        description="Maximum tokens per AI request"
    )
    
    AI_TEMPERATURE: float = Field(
        default=0.2,
        description="Temperature for AI responses (0.0=deterministic, 1.0=random)"
    )
    
    AI_REQUEST_TIMEOUT: int = Field(
        default=30,
        description="Timeout for AI API calls (seconds)"
    )
    
    AI_MAX_RETRIES: int = Field(
        default=3,
        description="Maximum retries for failed AI API calls"
    )
    
    # ======================================================================
    # FEATURE FLAGS & LIMITS
    # ======================================================================
    
    ENABLE_OCR: bool = Field(
        default=True,
        description="Enable OCR processing for document images"
    )
    
    ENABLE_HUMAN_REVIEW_MODE: bool = Field(
        default=True,
        description="Enable SME review workflow for AI-generated questions"
    )
    
    MAX_UPLOAD_FILE_SIZE_MB: int = Field(
        default=15,
        description="Maximum allowed file upload size (MB)"
    )
    
    ALLOWED_FILE_TYPES: str = Field(
        default="application/pdf,text/plain,application/vnd.ms-powerpoint",
        description="Comma-separated list of allowed MIME types"
    )
    
    DEFAULT_NUM_QUESTIONS_PER_QUIZ: int = Field(
        default=5,
        description="Default number of questions per quiz"
    )
    
    MIN_CONFIDENCE_FOR_CONFIRMED_GAP: float = Field(
        default=0.7,
        description="Minimum confidence score (0-1) to confirm a gap"
    )
    
    MAX_RECOMMENDATIONS_PER_GAP: int = Field(
        default=2,
        description="Maximum course recommendations per gap"
    )
    
    # ======================================================================
    # LOGGING & MONITORING
    # ======================================================================
    
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    LOG_FORMAT: str = Field(
        default="text",
        description="Log format: 'json' or 'text'"
    )
    
    ENABLE_REQUEST_LOGGING: bool = Field(
        default=True,
        description="Log all API requests and responses"
    )
    
    LOG_FILE_PATH: Optional[str] = Field(
        default=None,
        description="Path to log file (None = console only)"
    )
    
    LOG_FILE_MAX_SIZE_MB: int = Field(
        default=100,
        description="Maximum log file size before rotation (MB)"
    )
    
    LOG_FILE_BACKUP_COUNT: int = Field(
        default=5,
        description="Number of backup log files to keep"
    )
    
    # ======================================================================
    # SECURITY & CORS
    # ======================================================================
    
    BACKEND_BASE_URL: str = Field(
        default="http://localhost:8000",
        description="Backend API base URL"
    )
    
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Comma-separated list of allowed CORS origins"
    )
    
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="API rate limit (requests per minute per IP)"
    )
    
    ENABLE_API_KEY_AUTH: bool = Field(
        default=False,
        description="Require API key authentication"
    )
    
    # ======================================================================
    # EMAIL & NOTIFICATIONS
    # ======================================================================
    
    EMAIL_PROVIDER: str = Field(
        default="mock",
        description="Email provider: 'smtp', 'sendgrid', 'aws_ses', 'mock'"
    )
    
    SMTP_HOST: Optional[str] = Field(
        default=None,
        description="SMTP server hostname"
    )
    
    SMTP_PORT: int = Field(
        default=587,
        description="SMTP server port"
    )
    
    SMTP_USERNAME: Optional[str] = Field(
        default=None,
        description="SMTP authentication username"
    )
    
    SMTP_PASSWORD: Optional[str] = Field(
        default=None,
        description="SMTP authentication password"
    )
    
    SMTP_FROM_EMAIL: str = Field(
        default="noreply@statskill-ai.gov.in",
        description="Sender email address"
    )
    
    SENDGRID_API_KEY: Optional[str] = Field(
        default=None,
        description="SendGrid API key"
    )
    
    ENABLE_EMAIL_NOTIFICATIONS: bool = Field(
        default=False,
        description="Enable email notifications"
    )
    
    NOTIFICATION_EMAIL_RECIPIENT: str = Field(
        default="admin@statskill-ai.gov.in",
        description="Email address for notifications"
    )
    
    # ======================================================================
    # CACHING & SESSION
    # ======================================================================
    
    CACHE_PROVIDER: str = Field(
        default="memory",
        description="Cache provider: 'redis', 'memory', 'none'"
    )
    
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL"
    )
    
    SESSION_TIMEOUT_MINUTES: int = Field(
        default=30,
        description="Session timeout in minutes"
    )
    
    # ======================================================================
    # EXTERNAL SERVICE INTEGRATIONS
    # ======================================================================
    
    IGOT_API_URL: Optional[str] = Field(
        default=None,
        description="iGOT Karmayogi API base URL"
    )
    
    IGOT_API_KEY: Optional[str] = Field(
        default=None,
        description="iGOT Karmayogi API key"
    )
    
    IGOT_CLIENT_ID: Optional[str] = Field(
        default=None,
        description="iGOT Karmayogi OAuth client ID"
    )
    
    IGOT_CLIENT_SECRET: Optional[str] = Field(
        default=None,
        description="iGOT Karmayogi OAuth client secret"
    )
    
    APAR_LEDGER_API_URL: Optional[str] = Field(
        default=None,
        description="MoSPI APAR Ledger API URL"
    )
    
    APAR_LEDGER_API_KEY: Optional[str] = Field(
        default=None,
        description="MoSPI APAR Ledger API key"
    )
    
    # ======================================================================
    # FILE STORAGE
    # ======================================================================
    
    STORAGE_BACKEND: str = Field(
        default="local",
        description="Storage backend: 'local', 'aws_s3', 'gcs', 'azure_blob'"
    )
    
    LOCAL_STORAGE_PATH: str = Field(
        default="./uploads",
        description="Local storage directory path"
    )
    
    AWS_S3_BUCKET: Optional[str] = Field(
        default=None,
        description="AWS S3 bucket name"
    )
    
    AWS_S3_REGION: Optional[str] = Field(
        default=None,
        description="AWS S3 region"
    )
    
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        default=None,
        description="AWS access key ID"
    )
    
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default=None,
        description="AWS secret access key"
    )
    
    GCS_BUCKET: Optional[str] = Field(
        default=None,
        description="Google Cloud Storage bucket name"
    )
    
    GCS_PROJECT_ID: Optional[str] = Field(
        default=None,
        description="Google Cloud project ID"
    )
    
    # ======================================================================
    # OBSERVABILITY & TRACING
    # ======================================================================
    
    TRACING_BACKEND: str = Field(
        default="none",
        description="Tracing backend: 'jaeger', 'datadog', 'none'"
    )
    
    JAEGER_AGENT_HOST: Optional[str] = Field(
        default=None,
        description="Jaeger agent host"
    )
    
    JAEGER_AGENT_PORT: int = Field(
        default=6831,
        description="Jaeger agent port"
    )
    
    DATADOG_API_KEY: Optional[str] = Field(
        default=None,
        description="Datadog API key"
    )
    
    DATADOG_ENVIRONMENT: str = Field(
        default="development",
        description="Datadog environment"
    )
    
    ENABLE_METRICS: bool = Field(
        default=False,
        description="Enable performance metrics collection"
    )
    
    # ======================================================================
    # TESTING & DEVELOPMENT
    # ======================================================================
    
    USE_MOCKS: bool = Field(
        default=False,
        description="Use mock implementations of external services"
    )
    
    SEED_DEMO_DATA: bool = Field(
        default=True,
        description="Seed database with demo data on startup"
    )
    
    RESET_DATABASE_ON_STARTUP: bool = Field(
        default=False,
        description="Reset database on startup (development only)"
    )
    
    ENABLE_DOCS: bool = Field(
        default=True,
        description="Enable API documentation endpoints"
    )
    
    # ======================================================================
    # VALIDATORS
    # ======================================================================
    
    @field_validator('ENV')
    @classmethod
    def validate_env(cls, v: str) -> str:
        """Validate environment value."""
        valid_envs = {'development', 'staging', 'production'}
        if v not in valid_envs:
            raise ValueError(f"ENV must be one of {valid_envs}, got '{v}'")
        return v
    
    @field_validator('AI_PROVIDER')
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        """Validate AI provider value."""
        valid_providers = {'mock', 'gemini', 'openai', 'anthropic'}
        if v not in valid_providers:
            raise ValueError(f"AI_PROVIDER must be one of {valid_providers}, got '{v}'")
        return v
    
    @field_validator('AI_TEMPERATURE')
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"AI_TEMPERATURE must be between 0.0 and 1.0, got {v}")
        return v
    
    @field_validator('MIN_CONFIDENCE_FOR_CONFIRMED_GAP')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence score is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"MIN_CONFIDENCE_FOR_CONFIRMED_GAP must be between 0.0 and 1.0, got {v}")
        return v
    
    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def validate_origins(cls, v: str) -> List[str]:
        """Parse comma-separated origins list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    def validate_required_for_production(self) -> None:
        """
        Validate that all required variables are set for production.
        
        Raises:
            ValueError: If required variables are missing in production environment
        """
        if self.ENV == "production":
            required_vars = {
                'SECRET_KEY': self.SECRET_KEY,
                'DATABASE_URL': self.DATABASE_URL,
                'AI_API_KEY': self.AI_API_KEY,
            }
            
            missing = [var for var, value in required_vars.items() if not value]
            if missing:
                raise ValueError(
                    f"Production environment requires these variables: {', '.join(missing)}"
                )
            
            # Security checks for production
            if self.DEBUG:
                logger.warning("⚠️  DEBUG mode is enabled in production environment!")
            
            if self.RESET_DATABASE_ON_STARTUP:
                raise ValueError("RESET_DATABASE_ON_STARTUP must be False in production")
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"  # Ignore extra environment variables
        case_sensitive = True


def get_settings() -> Settings:
    """
    Get the application settings instance.
    
    This function loads and validates settings from environment variables and .env file.
    It performs security checks appropriate to the environment.
    
    Returns:
        Settings: Validated settings instance
        
    Raises:
        ValidationError: If environment variables are invalid
        ValueError: If required variables are missing in production
    """
    try:
        settings = Settings()
        
        # Validate production requirements
        settings.validate_required_for_production()
        
        # Log configuration status (without sensitive values)
        logger.info(f"✅ Configuration loaded (ENV={settings.ENV}, AI_PROVIDER={settings.AI_PROVIDER})")
        
        return settings
    
    except ValidationError as e:
        logger.error("❌ Configuration validation failed:")
        for error in e.errors():
            logger.error(f"  - {error['loc'][0]}: {error['msg']}")
        raise
    
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        raise


# Singleton instance
try:
    settings = get_settings()
except Exception as e:
    logger.critical(f"Failed to initialize settings: {e}")
    # Create a minimal fallback configuration for error reporting
    settings = Settings(
        APP_NAME="StatSkill AI (Degraded Mode)",
        ENV="production",
        DEBUG=False
    )
    raise
