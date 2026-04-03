from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://drillsense:drillsense@db:5432/drillsense"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    device_offline_threshold_seconds: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
