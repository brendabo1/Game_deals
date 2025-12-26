"""
Funções auxiliares e utilitários
"""
import re
from typing import Tuple, Optional
from playwright.async_api import Page

from config import config
from utils.logger import logger


class PriceParser:
    """Parser para extrair informações de preço"""
    
    # Padrões regex pré-compilados para melhor performance
    PRICE_PATTERN = re.compile(r"R\$\s?\d{1,3}(\.\d{3})*,\d{2}")
    INSTALLMENTS_PATTERN = re.compile(r"\d+x\s*R\$\s?\d{1,3}(\.\d{3})*,\d{2}")
    
    @classmethod
    def parse_price_text(cls, text: str) -> Tuple[str, str]:
        """
        Extrai valor e parcelas de um texto
        
        Args:
            text: Texto contendo informações de preço
            
        Returns:
            Tupla (valor, parcelas)
        """
        try:
            # Normaliza texto
            text = text.replace("\n", " ").strip()
            
            # Extrai valor
            price_match = cls.PRICE_PATTERN.search(text)
            price = price_match.group(0) if price_match else "-"
            
            # Extrai parcelas ou identifica método de pagamento
            installments_match = cls.INSTALLMENTS_PATTERN.search(text)
            if installments_match:
                installments = installments_match.group(0)
            elif "cartão" in text.lower():
                installments = "cartão"
            else:
                installments = "-"
            
            return price, installments
            
        except Exception as e:
            logger.debug(f"Erro ao extrair preço do texto: {e}")
            return "-", "-"


async def wait_for_stable_state(page: Page, selector: str, timeout: int = 3000) -> int:
    """
    Aguarda até que a contagem de elementos se estabilize
    
    Args:
        page: Página Playwright
        selector: Seletor CSS dos elementos
        timeout: Timeout em milissegundos
        
    Returns:
        Contagem estável de elementos
    """
    import time
    
    start_time = time.time()
    last_count = 0
    stable_checks = 0
    
    while (time.time() - start_time) * 1000 < timeout:
        current_count = await page.locator(selector).count()
        
        if current_count == last_count:
            stable_checks += 1
            if stable_checks >= 2:  # Estável por 2 verificações
                return current_count
        else:
            stable_checks = 0
            last_count = current_count
        
        await page.wait_for_timeout(500)
    
    return last_count


async def safe_extract(coro, error_message: str, default=None):
    """
    Executa uma extração com tratamento seguro de erros
    
    Args:
        coro: Corrotina a ser executada
        error_message: Mensagem de erro para logging
        default: Valor padrão em caso de erro
        
    Returns:
        Resultado da extração ou valor padrão
    """
    try:
        return await coro
    except Exception as e:
        logger.debug(f"{error_message}: {e}")
        return default