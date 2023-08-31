from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    DATABASE_URL: str

    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STATIC_DIR: str = os.path.join(BASE_DIR, 'app/') + 'static/'
    STATIC_URL: str
    TEST_DIR: str = os.path.join(BASE_DIR, 'tests/')

    RABBITMQ_URL: str
    QUEUE_NAME: str

    GEO_SERVICE_BASE_URL: str

    model_config = SettingsConfigDict(case_sensitive=True, frozen=False, env_file='.env')


@lru_cache
def get_settings() -> Settings:
    return Settings()
