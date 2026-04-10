from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    SECRET_KEY: str
    FLASK_ENV: str = "development"
    
    # Database
    DATABASE_URL: str
    
    # Security
    AES_SECRET_KEY: str
    JWT_SECRET_KEY: str
    BCRYPT_LOG_ROUNDS: int = 14
    JWT_ACCESS_TOKEN_EXPIRES: int = 3600 # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES: int = 2592000 # 30 days
    
    # Socket.IO
    SOCKETIO_ASYNC_MODE: str = "eventlet"
    
    # Email Settings
    EMAIL_HOST: str
    EMAIL_PORT: int = 587
    EMAIL_USER: str
    EMAIL_PASSWORD: str
    EMAIL_FROM: str
    EMAIL_USE_TLS: bool = True
    EMAIL_USE_SSL: bool = False
    
    # Supabase (Media Storage)
    SUPABASE_URL: str = Field(..., validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"))
    SUPABASE_KEY: str = Field(..., validation_alias=AliasChoices("SUPABASE_KEY", "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"))
    SUPABASE_STORAGE_BUCKET: str = Field("media", validation_alias=AliasChoices("SUPABASE_STORAGE_BUCKET", "NEXT_PUBLIC_SUPABASE_BUCKET"))
    
    # AI Config
    AI_API_KEY: str = Field(None, validation_alias=AliasChoices("AI_API_KEY", "API_KEY"))
    AI_API_URL: str = Field("https://openrouter.ai/api/v1/chat/completions", validation_alias=AliasChoices("AI_API_URL", "API_URL"))
    AI_MODEL: str = Field("openai/gpt-3.5-turbo", validation_alias=AliasChoices("AI_MODEL", "MODEL"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

configs = Settings()
