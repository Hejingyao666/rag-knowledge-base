from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # LLM 配置
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-chat"

    # Embedding 配置
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://api.deepseek.com/v1"
    EMBEDDING_MODEL: str = "text-embedding-v2"

    # 存储配置
    CHROMA_PERSIST_DIR: str = "./vector_store"
    CHROMA_COLLECTION: str = "knowledge_base"
    UPLOAD_DIR: str = "./uploads"
    DATABASE_URL: str = "sqlite:///./knowledge_base.db"

    # RAG 参数
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 5

    ALLOWED_EXTENSIONS: List[str] = ["pdf", "txt", "docx", "md"]

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    class Config:
        env_file = ".env"


settings = Settings()