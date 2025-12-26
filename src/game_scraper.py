from utils.logger import logger
from offers_extractor import extrair_ofertas
from typing import Dict


async def game_scraper(page, jogo: Dict) -> Dict:
    """
    Processa um jogo individual com tratamento de erros robusto
    """
    resultado = {
        "jogo": jogo,
        "ofertas": [],
        "sucesso": False,
        "erro": None
    }
    
    try:        
        # Navega para a página do jogo com timeout configurável
        await page.goto(jogo["url"], timeout=45000, wait_until="networkidle")
        
        # Aguarda carregamento da página
        await page.wait_for_load_state("domcontentloaded", timeout=30000)
        
        # Extrai as ofertas
        ofertas = await extrair_ofertas(page)
        
        resultado["ofertas"] = ofertas
        resultado["sucesso"] = True
        
        #logger.info(f"✅ Jogo {jogo['posicao']} processado com {len(ofertas)} ofertas")
        
    except Exception as e:
        resultado["erro"] = str(e)
        logger.error(f"❌ Erro ao processar jogo {jogo['posicao']}: {e}")
        
        # Tenta uma abordagem alternativa se falhar
        try:
            logger.info("Tentando abordagem alternativa...")
            await page.reload(timeout=30000)
            await page.wait_for_timeout(5000)
            
            # Tenta extrair ofertas mesmo com erro
            ofertas = await extrair_ofertas(page)
            if ofertas:
                resultado["ofertas"] = ofertas
                resultado["sucesso"] = True
                logger.info(f"✅ Recuperado com {len(ofertas)} ofertas")
        except:
            pass
    
    return resultado
