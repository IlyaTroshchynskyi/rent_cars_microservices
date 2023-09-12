from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    ENV: str
    DYNAMODB_ENDPOINT: str
    USER_TABLE: str
    READ_CAPACITY_UNITS: int
    WRITE_CAPACITY_UNITS: int

    model_config = SettingsConfigDict(case_sensitive=True, frozen=False, env_file='.env')


@lru_cache
def get_settings() -> Settings:
    return Settings()
