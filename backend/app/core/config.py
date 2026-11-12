from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    environment: str = "development"
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    admin_emails: str = ""
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    sqlalchemy_echo: bool = False

    # Provider credentials are optional so local Ollama deployments do not
    # require placeholder cloud secrets.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemma-4-31b-it:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    llm_provider: str = "ollama"
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434/v1"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    # CPU entailment model used to check that answer sentences are supported
    # by the sources they cite.
    grounding_model: str = "cross-encoder/nli-deberta-v3-xsmall"
    grounding_min_entailment: float = 0.5

    log_level: str = "INFO"
    log_format: str = "json"

    storage_backend: str = "local"
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_endpoint_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()  # pyright: ignore[reportCallIssue]


def is_admin_email(email: str) -> bool:
    return email.lower() in {
        value.strip().lower()
        for value in settings.admin_emails.split(",")
        if value.strip()
    }
