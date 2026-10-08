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

    # Provider credentials are optional so local Ollama deployments do not
    # require placeholder cloud secrets.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    llm_provider: str = "ollama"
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434/v1"

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
