from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://transfer:transfer@localhost:5432/transfer"
    currency: str = "RUB"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
