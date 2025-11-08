import os
class Settings:
    ENV: str = os.getenv("ENV", "dev")
    API_TITLE: str = os.getenv("API_TITLE", "FFmpeg API")
    API_VERSION: str = os.getenv("API_VERSION", "1.0.0")
    API_DESCRIPTION: str = os.getenv("API_DESCRIPTION", "Microservicio modular para procesamiento de video con FFmpeg.")
    DOCS_ENABLED: bool = os.getenv("DOCS_ENABLED", "true").lower() == "true"
    API_KEY: str = os.getenv("API_KEY", "")
    MAX_PARALLEL_DOWNLOADS: int = int(os.getenv("MAX_PARALLEL_DOWNLOADS", "4"))
    DOWNLOAD_TIMEOUT: float | None = (float(os.getenv("DOWNLOAD_TIMEOUT", "0")) or None)
settings = Settings()
