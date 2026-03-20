from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'AI Campus Recruit Platform'
    cors_origins: str = '*'

    database_url: str = (
        'mysql+pymysql://root:root@127.0.0.1:3306/campus_recruit?charset=utf8mb4'
    )
    redis_url: str = 'redis://127.0.0.1:6379/0'

    jwt_secret_key: str = 'change-this-in-production'
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 60 * 24

    # RAG settings
    rag_chunk_size: int = 400
    rag_chunk_overlap: int = 80
    rag_top_k: int = 5
    embedding_model: str = 'paraphrase-multilingual-MiniLM-L12-v2'

    # LLM API (OpenAI-compatible)
    llm_api_key: str = ''
    llm_base_url: str = 'https://api.openai.com/v1'
    llm_model: str = 'gpt-3.5-turbo'


settings = Settings()
