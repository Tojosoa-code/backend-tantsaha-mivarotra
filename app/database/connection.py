"""
Connexion à la base de données PostgreSQL
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Créer le moteur de base de données
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Vérifier la connexion avant utilisation
    echo=settings.DEBUG   # Logger les requêtes SQL en mode debug
)

# Créer la session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()


def get_db():
    """
    Générateur de session de base de données

    Utilisé comme dépendance FastAPI pour obtenir une session DB.
    La session est automatiquement fermée après utilisation.

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
