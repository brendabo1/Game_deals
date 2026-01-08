import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from playwright.async_api import async_playwright
from typing import List, Dict
import uvicorn

# Configurações do Scraper
BASE_URL = "https://www.comparajogos.com.br"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Board Game Deals API")

async def extrair_ofertas_da_pagina(page) -> List[Dict]:
    lista_ofertas = []
    try:
        painel_ativo = page.locator("div[role='tabpanel']:not([hidden])")
        btn_mostrar_mais = painel_ativo.locator("button:has-text('Mostrar mais')")
        
        if await btn_mostrar_mais.count() > 0:
            btn = btn_mostrar_mais.last
            if await btn.is_visible():
                await btn.scroll_into_view_if_needed()
                await btn.click()
                await page.wait_for_timeout(1000)

        cards = painel_ativo.locator("div.relative.rounded-lg.my-2.p-1")
        total_cards = await cards.count()

        for i in range(total_cards):
            card = cards.nth(i)
            loja_el = card.locator("div.truncate.text-sm")
            loja = await loja_el.get_attribute("title") or await loja_el.inner_text() if await loja_el.count() > 0 else "Desconhecida"

            info_oferta = {"loja": loja.strip(), "cartao": "-", "pix": "-", "link": ""}
            
            link_el = card.locator("a.group[href*='/api/redirect']")
            if await link_el.count() > 0:
                info_oferta["link"] = BASE_URL + await link_el.first.get_attribute("href")

            precos_divs = card.locator("div.flex.items-center.text-green-800")
            for j in range(await precos_divs.count()):
                bloco = precos_divs.nth(j)
                v_reais = bloco.locator("span.font-semibold")
                v_cents = bloco.locator("span.text-\\[0\\.6em\\]")
                
                valor = "R$ 0,00"
                if await v_reais.count() > 0:
                    valor = f"R$ {await v_reais.inner_text()},{await v_cents.inner_text() if await v_cents.count() > 0 else '00'}"
                
                mod_txt = (await bloco.locator("small").inner_text()).lower() if await bloco.locator("small").count() > 0 else ""
                if "pix" in mod_txt: info_oferta["pix"] = valor
                else: info_oferta["cartao"] = valor

            lista_ofertas.append(info_oferta)
    except Exception as e:
        logger.error(f"Erro na extração: {e}")
    return lista_ofertas


@app.get("/jogos-populares")
async def get_popular_games():
    """
    Retorna a lista dos 20 jogos populares e suas ofertas em tempo real.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent='Mozilla/5.0...')
        page = await context.new_page()
        
        try:
            await page.goto(BASE_URL, wait_until="domcontentloaded")
            await page.wait_for_selector("h2:has-text('Populares da Semana')")
            
            container = page.locator("div:has(> h2:has-text('Populares da Semana'))").locator("xpath=..")
            cards = container.locator("div.snap-start")
            
            jogos_com_ofertas = []
            
            total_para_processar = min(await cards.count(), 20)
            
            links_jogos = []
            for i in range(total_para_processar):
                card = cards.nth(i)
                nome = await card.locator("div.vertical-wrap").get_attribute("title")
                href = await card.locator("a.group").get_attribute("href")
                if nome and href:
                    links_jogos.append({"nome": nome, "url": BASE_URL + href})

            for jogo in links_jogos:
                await page.goto(jogo["url"], wait_until="domcontentloaded")
                await page.wait_for_timeout(1500) # Espera carregar ofertas
                ofertas = await extrair_ofertas_da_pagina(page)
                jogo["ofertas"] = ofertas
                jogos_com_ofertas.append(jogo)

            return {"total": len(jogos_com_ofertas), "data": jogos_com_ofertas}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            await browser.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)