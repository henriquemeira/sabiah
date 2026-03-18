"""Módulo de gerenciamento do banco de dados SQLite."""

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings
from src.models import Base

settings = get_settings()


def get_engine():
    """Cria e retorna o engine do SQLAlchemy."""
    # Garante que o diretório de dados existe
    data_dir = Path(settings.database_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    engine = create_engine(
        settings.database_url,
        echo=False,  # Set True para debug SQL
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    )
    return engine


def get_session_factory():
    """Retorna a factory de sessões."""
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Inicializa o banco de dados criando todas as tabelas."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    """Remove todas as tabelas do banco de dados."""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)


# Instância global da session factory
_session_factory = None


def get_db() -> Generator[Session, None, None]:
    """Dependency para obter sessões do banco de dados."""
    global _session_factory
    if _session_factory is None:
        _session_factory = get_session_factory()
    
    db = _session_factory()
    try:
        yield db
    finally:
        db.close()
