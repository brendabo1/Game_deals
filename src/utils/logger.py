"""
Configuração centralizada de logging
"""
import logging
from config import config


def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Configura e retorna um logger com formatação consistente
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evitar configuração múltipla
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(config.LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    return logger


# Logger global para o projeto
logger = setup_logger("src")