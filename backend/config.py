"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Union, List
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # App settings
    app_name: str = "E-commerce Fulfillment Control Tower"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"
    
    # Database paths
    wms_db_path: str = "./data/wms.db"
    oms_db_path: str = "./data/oms.db"
    tms_db_path: str = "./data/tms.db"
    billing_db_path: str = "./data/billing.db"
    returns_db_path: str = "./data/returns.db"
    yard_db_path: str = "./data/yard.db"
    
    # API settings
    api_prefix: str = "/api/v1"
    cors_origins: Union[str, List[str]] = "http://localhost:3000,http://localhost:5173"
    
    # Chat/LLM settings
    chat_api_url: str = "https://ea055412564a.ngrok-free.app/v1/chat/completions"
    chat_model_name: str = ""
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v


settings = Settings()
