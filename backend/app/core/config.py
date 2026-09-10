from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    database_url: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    openrouter_api_key: str

    gemini_api_key: str
    gemini_model: str

    llm_provider: str
    ollama_model: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()