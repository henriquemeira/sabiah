"""Módulo de configuração de logging."""

import logging
import sys
from pathlib import Path

# Configuração básica
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO, log_file: str | None = None) -> logging.Logger:
    """
    Configura o sistema de logging da aplicação.
    
    Args:
        level: Nível de logging (default: INFO)
        log_file: Caminho opcional para arquivo de log
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger("sabiah")
    logger.setLevel(level)
    
    # Remove handlers existentes
    logger.handlers.clear()
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo (se especificado)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# Logger padrão
logger = setup_logging()
