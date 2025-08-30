# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    TODOIST_CLIENT_ID: str = Field(...)
    TODOIST_CLIENT_SECRET: str = Field(...)
    TODOIST_REDIRECT_URI: str = "http://localhost:5173/api/oauth/callback"
    FRONTEND_BASE: str = "http://localhost:5173"
    SESSION_SECRET: str = "change-me"
    # Comma-separate in .env OR override in code
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    SAME_SITE_NONE: bool = False  # set True if you’re doing cross-origin cookies in dev

    # pydantic-settings v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unexpected envs
    )

settings = Settings()
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    TODOIST_CLIENT_ID: str = Field(...)
    TODOIST_CLIENT_SECRET: str = Field(...)
    TODOIST_REDIRECT_URI: str = "http://localhost:5173/api/oauth/callback"
    FRONTEND_BASE: str = "http://localhost:5173"
    SESSION_SECRET: str = "change-me"
    # Comma-separate in .env OR override in code
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    SAME_SITE_NONE: bool = False  # set True if you’re doing cross-origin cookies in dev

    # pydantic-settings v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unexpected envs
    )

settings = Settings()
