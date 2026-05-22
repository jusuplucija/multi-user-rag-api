from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multi-User RAG API"
    app_version: str = "1.0.0"

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str
    openai_api_key: str = ""

    vector_db_path: str = "./chroma_db"
    storage_path: str = "./storage"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()