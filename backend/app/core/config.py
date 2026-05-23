# app/core/config.py
# Application settings loaded from environment variables / .env file.

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    supabase_anon_key: str
    frontend_url: str = "http://localhost:3000"
    max_upload_mb: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
