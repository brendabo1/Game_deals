import asyncio
from popular_games_extractor import extrair_populares_da_semana
from game_scraper import game_scraper
from utils.logger import logger
from config import config
from playwright.async_api import async_playwright


async def executar_scraper(headless=True):
    """
    Função principal do scraper
    """
    async with async_playwright() as p:
        # Configura o browser com opções para melhor performance
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Configura timeouts
        page.set_default_timeout(60000)  # 60 segundos
        page.set_default_navigation_timeout(60000)
        
        # Desativa recursos desnecessários para melhor performance
        await page.route("**/*.{png,jpg,jpeg,gif,svg,webp}", lambda route: route.abort())
        
        try:
            await page.goto(config.BASE_URL, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            logger.info("Jogos populares da semana...")
            jogos = await extrair_populares_da_semana(page)
            
            logger.info(f"Total de jogos para processar: {len(jogos)}")
            
            resultados = []
            
            for jogo in jogos:
                print(f"\n{'='*70}")
                print(f"🎮 {jogo['posicao']}. {jogo['nome']}")
                print(f"{'='*70}")
                
                resultado = await game_scraper(page, jogo)
                resultados.append(resultado)
                
                if resultado["sucesso"] and resultado["ofertas"]:
                    for oferta in resultado["ofertas"]:
                        print(f"\n   🏪 {oferta['loja']}")
                        print(f"      💳 Cartão: {oferta['cartao']} ({oferta['parcelas']})")
                        print(f"      ⚡ Pix: {oferta['pix']}")
                        print(f"      🔗 Link: {oferta.get('link', 'Não disponível')}")
                else:
                    print(f"   ⚠️ Nenhuma oferta")
                    if resultado["erro"]:
                        print(f"   ❌ Erro: {resultado['erro']}")
                
                # Pequena pausa entre jogos para evitar bloqueios
                await page.wait_for_timeout(2000)
            
            # Resumo final
            print(f"\n{'='*70}")
            print("📊 RESUMO FINAL")
            print(f"{'='*70}")
            
            sucessos = sum(1 for r in resultados if r["sucesso"])
            total_ofertas = sum(len(r["ofertas"]) for r in resultados)
            
            print(f"✅ Jogos processados com sucesso: {sucessos}/{len(jogos)}")
            print(f"📈 Total de ofertas coletadas: {total_ofertas}")
            
            for resultado in resultados:
                if not resultado["sucesso"]:
                    print(f"❌ Falha: {resultado['jogo']['nome']} - {resultado['erro']}")
            
        except Exception as e:
            logger.error(f"Erro fatal no scraper: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    # Executa o scraper
    asyncio.run(executar_scraper(headless=True))