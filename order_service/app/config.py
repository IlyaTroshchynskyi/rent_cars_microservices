from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    MONGODB_URI: str
    MONGODB_DB_NAME: str

    CAR_SERVICE_BASE_URL: str
    AUTH_SERVICE_BASE_URL: str

    model_config = SettingsConfigDict(case_sensitive=True, frozen=True, env_file='.env')


@lru_cache
def get_settings() -> Settings:
    return Settings()
