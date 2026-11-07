from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_port: int
    db_host: str
    currency: str
    kafka_bootstrap_servers: str
    kafka_security_protocol: str = "PLAINTEXT"
    kafka_sasl_mechanism: str | None = None
    kafka_sasl_username: str | None = None
    kafka_sasl_password: str | None = None
    kafka_group_id: str = "transfer-service"
    kafka_enabled: bool = True
    kafka_booking_topic: str = "transfer.booking"
    kafka_cancel_topic: str = "transfer.booking.cancel"
    kafka_status_topic: str = "transfer.booking-status"
    kafka_cancellation_result_topic: str = "transfer.cancellation-result"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
