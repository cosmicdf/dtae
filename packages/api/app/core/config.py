from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DTAE_", env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "dtae_tools"

    embedding_model: str = "nomic-ai/nomic-embed-text-v1.5"
    max_tools_default: int = 8
    max_tool_tokens_default: int = 2000

    cors_origins: list[str] = ["*"]


settings = Settings()
