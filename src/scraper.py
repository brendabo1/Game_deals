import asyncio
import re
import logging
from playwright.async_api import async_playwright
from typing import List, Dict

BASE_URL = "https://www.comparajogos.com.br"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def extrair_populares_da_semana(page) -> List[Dict]:
    """
    Localiza especificamente a seção 'Populares da Semana' e extrai os 20 jogos.
    """
    jogos = []
    try:
        # 1. Localiza o título da seção
        titulo_secao = page.locator("h2:has-text('Populares da Semana')")
        await titulo_secao.wait_for(state="visible", timeout=15000)
        
        # 2. Localiza o carrossel de jogos populares
        container_secao = page.locator("div:has(> h2:has-text('Populares da Semana'))").locator("xpath=..")
        
        # 3. Busca apenas os cards 
        cards = container_secao.locator("div.snap-start")
        total_cards = await cards.count()
        
        logger.info(f"Detectados {total_cards} cards na seção Populares.")

        for i in range(min(total_cards, 20)):
            card = cards.nth(i)
            
            # Extração do nome via title 
            nome_el = card.locator("div.vertical-wrap")
            nome = await nome_el.get_attribute("title")
            
            # Extração do link
            link_el = card.locator("a.group")
            href = await link_el.get_attribute("href")

            if nome and href:
                jogos.append({
                    "posicao": f"{i+1}º",
                    "nome": nome.strip(),
                    "url": BASE_URL + href if href.startswith('/') else href
                })
                
    except Exception as e:
        logger.error(f"Erro ao isolar a seção de populares: {e}")
    
    return jogos

async def extrair_ofertas_da_pagina(page) -> List[Dict]:
    lista_ofertas = []
    
    try:
        # 1. Localizamos o container principal de ofertas 
        painel_ativo = page.locator("div[role='tabpanel']:not([hidden])")
        
        # 2. Expansão de ofertas
        btn_mostrar_mais = painel_ativo.locator("button:has-text('Mostrar mais')")
        
        if await btn_mostrar_mais.count() > 0:
            btn = btn_mostrar_mais.last
            if await btn.is_visible():
                logger.info(f"Expandindo ofertas para o jogo...")
                await btn.scroll_into_view_if_needed()
                await btn.click()
                await page.wait_for_timeout(1500)

        # 3. Localiza os cards de oferta dentro do painel
        cards = painel_ativo.locator("div.relative.rounded-lg.my-2.p-1")
        total_cards = await cards.count()
        logger.info(f"Processando {total_cards} ofertas no painel ativo.")

        for i in range(total_cards):
            card = cards.nth(i)
            
            # Extração da Loja
            loja = "Desconhecida"
            loja_el = card.locator("div.truncate.text-sm")
            if await loja_el.count() > 0:
                loja = await loja_el.get_attribute("title") or await loja_el.inner_text()

            # Link de Redirecionamento
            link_final = ""
            link_el = card.locator("a.group[href*='/api/redirect']")
            if await link_el.count() > 0:
                href = await link_el.first.get_attribute("href")
                link_final = BASE_URL + href if href.startswith('/') else href

            # Preços
            blocos_preco = card.locator("div.flex.items-center.text-green-800")
            num_precos = await blocos_preco.count()
            
            info_oferta = {
                "loja": loja.strip(),
                "cartao": "-",
                "parcelas": "-",
                "pix": "-",
                "link": link_final
            }

            for j in range(num_precos):
                bloco = blocos_preco.nth(j)
                v_reais = bloco.locator("span.font-semibold")
                v_cents = bloco.locator("span.text-\\[0\\.6em\\]")
                
                valor_str = "-"
                if await v_reais.count() > 0:
                    r = await v_reais.inner_text()
                    c = await v_cents.inner_text() if await v_cents.count() > 0 else "00"
                    valor_str = f"R$ {r},{c}"
                
                modalidade_el = bloco.locator("small")
                mod_txt = (await modalidade_el.inner_text()).lower() if await modalidade_el.count() > 0 else ""

                if "pix" in mod_txt:
                    info_oferta["pix"] = valor_str
                else:
                    info_oferta["cartao"] = valor_str
                    info_oferta["parcelas"] = mod_txt.strip()

            lista_ofertas.append(info_oferta)

    except Exception as e:
        logger.error(f"Erro crítico na extração de ofertas: {e}")
            
    return lista_ofertas

async def executar_scraper(headless=True):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        page.set_default_timeout(60000)

        try:
            logger.info(f"Acessando {BASE_URL}...")
            await page.goto(BASE_URL, wait_until="domcontentloaded")
            
            jogos_populares = await extrair_populares_da_semana(page)
            logger.info(f"Iniciando análise de {len(jogos_populares)} jogos populares...")

            for jogo in jogos_populares:
                print(f"\n🚀 Acessando {jogo['posicao']}: {jogo['nome']}")
                
                # Navega para a página interna do jogo
                await page.goto(jogo["url"], wait_until="domcontentloaded")
                
                await page.wait_for_timeout(2500) 
                
                ofertas = await extrair_ofertas_da_pagina(page)
                
                if ofertas:
                    for o in ofertas:
                        print(f"  [LOJA] {o['loja']} | PIX: {o['pix']} | CARTÃO: {o['cartao']} ({o['parcelas']}) Link: {o['link']}")
                else:
                    print("  [AVISO] Nenhuma oferta encontrada para este item.")
                
                await page.wait_for_timeout(1000)

            print(f"\n✅ Scraping concluído com sucesso!")

        except Exception as e:
            logger.error(f"Erro no fluxo principal: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(executar_scraper(headless=False))