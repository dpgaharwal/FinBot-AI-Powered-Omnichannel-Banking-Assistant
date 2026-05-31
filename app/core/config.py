from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str

    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str
    LANGCHAIN_TRACING_V2: str

    class Config:
        env_file = ".env"

settings = Settings()