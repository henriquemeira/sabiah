"""Módulo de configuração centralizada do Sabiah."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações do aplicação."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")

    # Google Gemini
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")

    # Groq (alternativa gratuita ao Gemini)
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")

    # Banco de Dados
    database_path: str = Field(default="data/sabiah.db", alias="DATABASE_PATH")

    # ChromaDB
    chroma_persist_directory: str = Field(
        default="data/chroma_db", alias="CHROMA_PERSIST_DIRECTORY"
    )

    # Freshdesk (Futuro)
    freshdesk_api_key: str = Field(default="", alias="FRESHDESK_API_KEY")
    freshdesk_subdomain: str = Field(default="", alias="FRESHDESK_SUBDOMAIN")
    
    # Telegram Grupo
    telegram_grupo_id: str = Field(default="", alias="TELEGRAM_GRUPO_ID")

    # Caminhos
    @property
    def database_url(self) -> str:
        """Retorna URL do banco de dados para SQLAlchemy."""
        return f"sqlite:///{self.database_path}"

    @property
    def data_dir(self) -> Path:
        """Retorna o diretório de dados."""
        return Path(self.database_path).parent


@lru_cache
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()
