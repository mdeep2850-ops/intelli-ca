from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Intelli-CA"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./data/sql_app.db"
    GOOGLE_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:5173"
    DATA_DIR: str = "./data"
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024 # 10 MB limit
    
    # Embeddings
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-2"
    
    # Agent Execution
    MAX_AGENT_STEPS: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
