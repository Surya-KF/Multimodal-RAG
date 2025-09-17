from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseModel):
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    chroma_persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./vector_db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_port: int = int(os.getenv("FRONTEND_PORT", "8501"))
    vosk_model_path: str = os.getenv("VOSK_MODEL_PATH", "./models/vosk-model-en-us-0.22")
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))

_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
