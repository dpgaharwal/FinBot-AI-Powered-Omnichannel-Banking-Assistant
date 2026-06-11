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

    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_DATABASE: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str

    QDRANT_HOST: str
    QDRANT_PORT: int
    QDRANT_COLLECTION: str

    EMBEDDING_MODEL: str

    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_FROM: str
    TWILIO_AUTH_TOKEN_WEBHOOK: str

    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    RABBITMQ_URL: str

    class Config:
        env_file = ".env"

settings = Settings()