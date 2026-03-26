
"""
Configuration du Backend FastAPI
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuration de l'application"""

    # Base de données
    DATABASE_URL: str = "postgresql://tantsaha_admin:tantsaha2024@localhost:5432/tantsaha_mivarotra"

    # Sécurité
    SECRET_KEY: str = "ccoo111185fdffefsdf2ez1541jy520g2s111111f22sf8s5#fdf88720"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Serveur
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # Algorithmes - Paramètres
    MIN_MATCHING_SCORE: float = 70.0
    MAX_ROUTE_DISTANCE_KM: float = 100.0
    SEARCH_MAX_RESULTS: int = 20

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Obtenir les paramètres de configuration (avec cache)"""
    return Settings()
