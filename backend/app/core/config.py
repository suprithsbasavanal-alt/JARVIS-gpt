import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str = Field(default="")
    ANTHROPIC_API_KEY: str = Field(default="")
    GEMINI_API_KEY: str = Field(default="")
    
    # Databases & Caching
    DATABASE_URL: str = Field(default="postgresql://jarvis_user:jarvis_password@localhost:5432/jarvis_db")
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # Model Configuration
    PLANNER_PRIMARY_MODEL: str = Field(default="qwen2.5:7b")
    PLANNER_FALLBACK_MODEL: str = Field(default="llama3.2:3b")
    EXECUTOR_PRIMARY_MODEL: str = Field(default="llama3:8b")
    EXECUTOR_FALLBACK_MODEL: str = Field(default="phi3:medium")

    
    # Audio Setup
    WAKE_WORDS: str = Field(default="jarvis,hey jarvis")
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
