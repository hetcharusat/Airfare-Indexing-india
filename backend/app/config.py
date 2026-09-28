import os

class Settings:
    PROJECT_NAME: str = "APIx Production Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./backend/data/apix.db")
    CORS_ORIGINS: list = ["*"]
    HEADLESS_SCRAPER: bool = True
    BOOTSTRAP_RUNS: int = 150

settings = Settings()
