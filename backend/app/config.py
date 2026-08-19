from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@db:5432/traffic_sim",
        env="DATABASE_URL"
    )
    # Pour les scripts d'importation synchrones
    DATABASE_SYNC_URL: str = Field(
        default="postgresql://postgres:postgres@db:5432/traffic_sim",
        env="DATABASE_SYNC_URL"
    )

settings = Settings()
