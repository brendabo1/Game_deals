from utils.logger import logger
from config import config


async def extrair_populares_da_semana(page):
    """
    Extrai nome, ranking e URL dos jogos populares da semana
    """
    jogos = []

    try:
        # Aguarda o título da seção com timeout mais longo
        await page.wait_for_selector("span:has-text('Populares da Semana')", 
                                    timeout=15000, state="visible")

        # Usar um seletor mais robusto
        section = page.locator("span:has-text('Populares da Semana')").locator("xpath=ancestor::div[1]")
        
        # Aguarda os links aparecerem
        await page.wait_for_selector("a[href^='/item/']", timeout=10000)
        
        links = section.locator("a[href^='/item/']")
        
        total = await links.count()

        for i in range(total):
            link = links.nth(i)
            
            # Tenta múltiplas estratégias para pegar o nome
            nome = None
            try:
                # Método 1: Pelo atributo title
                nome = await link.locator("div[title]").get_attribute("title")
            except:
                try:
                    # Método 2: Pelo texto do elemento
                    nome = await link.locator("div[title]").inner_text()
                except:
                    # Método 3: Pelo texto do link
                    nome = await link.inner_text()
            
            href = await link.get_attribute("href")
            
            if nome and href:
                jogos.append({
                    "posicao": i + 1,
                    "nome": nome.strip(),
                    "url": config.BASE_URL + href
                })

    except Exception as e:
        logger.error(f"Erro ao extrair jogos populares: {e}")

    return jogos
