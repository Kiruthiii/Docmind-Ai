from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocMind AI API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Gemini API
    GEMINI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    CHAT_MODEL: str = "gemini-3.5-flash"
    
    # Supabase Setup
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # Ingestion settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    MAX_RETRIEVAL_CHUNKS: int = 15
    SIMILARITY_THRESHOLD: float = 0.1  # Set to 0.1 for high recall
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

