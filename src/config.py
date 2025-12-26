import os
from dataclasses import dataclass
from typing import Final

@dataclass
class Config:
    """Configurações do scraper"""
    
    # URLs
    BASE_URL: Final[str] = "https://www.comparajogos.com.br"
    
    # Timeouts (em milissegundos)
    TIMEOUT: Final[int] = 60000
    NAVIGATION_TIMEOUT: Final[int] = 45000
    DEFAULT_WAIT_TIMEOUT: Final[int] = 10000
    OFFER_EXPANSION_TIMEOUT: Final[int] = 3000
    
    # Configurações do navegador
    VIEWPORT_WIDTH: Final[int] = 1920
    VIEWPORT_HEIGHT: Final[int] = 1080
    USER_AGENT: Final[str] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Seletores CSS (mantidos como constantes para fácil manutenção)
    POPULAR_SECTION_SELECTOR: Final[str] = "span:has-text('Populares da Semana')"
    GAME_LINK_SELECTOR: Final[str] = "a[href^='/item/']"
    OFFER_CARD_SELECTOR: Final[str] = "div.relative.rounded-lg.my-2.p-1"
    SHOW_MORE_BUTTON_SELECTOR: Final[str] = "button:has-text('Mostrar mais')"
    OFFER_LINK_SELECTOR: Final[str] = "a[href^='/api/redirect']"
    STORE_NAME_SELECTOR: Final[str] = "div.mb-1.truncate"
    PRICE_BLOCK_SELECTOR: Final[str] = "div.group.select-none"
    PRICE_TEXT_SELECTOR: Final[str] = "div.text-green-800"
    OFFERS_SECTION_SELECTOR: Final[str] = "span:has-text('Ofertas')"
    
    # Configurações de logging
    LOG_FORMAT: Final[str] = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL: Final[str] = "INFO"
    
    # Limites e tentativas
    MAX_EXPANSION_ATTEMPTS: Final[int] = 5
    MAX_STALE_ATTEMPTS: Final[int] = 3
    RETRY_DELAY: Final[int] = 2000  # ms entre tentativas


# Instância única de configuração
config = Config()