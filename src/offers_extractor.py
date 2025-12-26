from utils.logger import logger
from config import config
from price_extractor import extrair_preco
from typing import List, Dict


async def expandir_todas_as_ofertas(page):
    """
    Estratégia robusta para expandir todas as ofertas
    """
    expand_offers = True
    tentativas = 0
    tentativas_sem_mudanca = 0
    
    
    #tentativas < tentativas_maximas and
    while expand_offers and tentativas_sem_mudanca < 5:
        try:
            # Conta os cards atuais
            cards_locator = page.locator(config.OFFER_CARD_SELECTOR)
            quantidade_atual = await cards_locator.count()
            
            #logger.info(f"Tentativa {tentativas + 1}: {quantidade_atual} ofertas encontradas")
            
            # Procura botão "Mostrar mais"
            botao_locator = page.locator(config.SHOW_MORE_BUTTON_SELECTOR)
            
            if await botao_locator.count() == 0:
                # Nenhum botão 'Mostrar mais' encontrado
                expand_offers = False
                break
                
            botao = botao_locator.first
            
            # Verifica se o botão está visível e habilitado
            if not await botao.is_visible():
                # logger.info("Botão não está visível")
                break
                
            # Tenta clicar com diferentes estratégias
            try:
                # Estratégia 1: Click normal
                await botao.click(timeout=5000)
            except:
                try:
                    # Estratégia 2: Click com force
                    await botao.click(force=True, timeout=3000)
                except:
                    try:
                        # Estratégia 3: Click via JavaScript
                        await page.evaluate("""(selector) => {
                            const btn = document.querySelector(selector);
                            if (btn) btn.click();
                        }""", "button:has-text('Mostrar mais')")
                    except:
                        logger.warning("Não foi possível clicar no botão")
                        break
            
            # Aguarda o carregamento dinâmico
            await page.wait_for_timeout(3000)  # Aguarda 3 segundos
            
            # Verifica se algo mudou
            nova_quantidade = await cards_locator.count()
            
            if nova_quantidade > quantidade_atual:
                #logger.info(f"✅ Carregadas {nova_quantidade - quantidade_atual} novas ofertas")
                expand_offers = False
            else:
                #logger.info("⚠️ Nenhuma nova oferta carregada")
                tentativas_sem_mudanca += 1
            
            tentativas += 1
            
            # Pequena pausa entre tentativas
            await page.wait_for_timeout(1500)
            
        except Exception as e:
            logger.error(f"Erro na tentativa {tentativas + 1}: {e}")
            break
    
    logger.info(f"Total de ofertas: {await page.locator('div.relative.rounded-lg.my-2.p-1').count()}")


async def extrair_ofertas(page) -> List[Dict]:
    """
    Extrai todas as ofertas de uma página de jogo
    """
    ofertas = []
    
    try:
        # Aguarda o carregamento da página
        await page.wait_for_load_state("networkidle", timeout=15000)
        
        # Verifica se a seção de ofertas existe
        try:
            await page.wait_for_selector("span:has-text('Ofertas')", timeout=10000, state="visible")
        except:
            logger.warning("Seção 'Ofertas' não encontrada")
            return ofertas
        
        # Expande todas as ofertas
        await expandir_todas_as_ofertas(page)
        
        # Aguarda um momento para garantir que tudo está carregado
        await page.wait_for_timeout(2000)
        
        # Localiza todos os cards de oferta
        cards_locator = page.locator("div.relative.rounded-lg.my-2.p-1")
        total_ofertas = await cards_locator.count()
                
        for i in range(total_ofertas):
            try:
                card = cards_locator.nth(i)

                link_oferta = None
                try:
                    # O link está geralmente em um elemento <a> dentro do card
                    link_element = card.locator("a[href^='/api/redirect']").first
                    if await link_element.count() > 0:
                        link_relativo = await link_element.get_attribute("href")
                        if link_relativo:
                            link_oferta = config.BASE_URL + link_relativo
                except Exception as e:
                    logger.debug(f"Erro ao extrair link da oferta {i+1}: {e}")
                
                # Extrair nome da loja
                loja = "Desconhecida"
                
                # Tenta múltiplas estratégias para obter o nome da loja
                try:
                    # Método 1: Pelo título da div
                    loja_element = card.locator("div.mb-1.truncate").first
                    if await loja_element.count() > 0:
                        loja_attr = await loja_element.get_attribute("title")
                        if loja_attr:
                            loja = loja_attr
                        else:
                            loja = await loja_element.inner_text()
                except:
                    try:
                        # Método 2: Pelo alt da imagem
                        img_element = card.locator("img").first
                        if await img_element.count() > 0:
                            alt_text = await img_element.get_attribute("alt")
                            if alt_text:
                                loja = alt_text
                    except:
                        try:
                            # Método 3: Pelo texto da loja
                            loja = await card.locator("div.mb-1.truncate").first.inner_text()
                        except:
                            pass
                
                # Extrair preços
                preco_cartao = "-"
                parcelas = "-"
                preco_pix = "-"
                
                # Localiza o bloco de preços
                bloco_preco = card.locator(config.PRICE_BLOCK_SELECTOR).first
                
                if await bloco_preco.count() > 0:
                    # Encontra todas as divs de preço
                    divs_preco = bloco_preco.locator(config.PRICE_TEXT_SELECTOR)
                    total_divs = await divs_preco.count()
                    
                    if total_divs >= 1:
                        # Primeiro bloco (cartão)
                        primeiro = divs_preco.nth(0)
                        preco_cartao, parcelas = await extrair_preco(primeiro)
                        
                        # Se não encontrou parcelas, tenta identificar
                        if parcelas == "-":
                            texto_primeiro = await primeiro.inner_text()
                            if "cartão" in texto_primeiro.lower():
                                parcelas = "cartão"
                    
                    if total_divs >= 2:
                        # Segundo bloco (pix)
                        segundo = divs_preco.nth(1)
                        texto_segundo = await segundo.inner_text()
                        
                        if "pix" in texto_segundo.lower():
                            preco_pix, _ = await extrair_preco(segundo)
                
                # Adiciona à lista de ofertas
                ofertas.append({
                    "loja": loja.strip() if isinstance(loja, str) else str(loja),
                    "cartao": preco_cartao,
                    "parcelas": parcelas,
                    "pix": preco_pix,
                    "link": link_oferta 
                })
                
            except Exception as e:
                logger.error(f"Erro ao processar oferta {i+1}: {e}")
                continue
        
        logger.info(f"✅ Extraídas {len(ofertas)} ofertas com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao extrair ofertas: {e}")
    
    return ofertas


async def processar_jogo(page, jogo: Dict) -> Dict:
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
        
        logger.info(f"✅ Jogo {jogo['posicao']} processado com {len(ofertas)} ofertas")
        
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
