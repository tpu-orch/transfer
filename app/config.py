from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_port: int
    db_host: str
    currency: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
