from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):

    RABBITMQ_URL: str
    QUEUE_NAME: str

    model_config = SettingsConfigDict(case_sensitive=True, frozen=False, env_file='.env')


@lru_cache
def get_settings() -> Settings:
    return Settings()
