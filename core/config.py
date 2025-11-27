from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    mongo_uri: str = Field(..., alias="MONGO_URI")
    secret_key: str = Field(..., alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    master_db_name: str = Field("org_master", alias="MASTER_DB_NAME")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()


settings = get_settings()
