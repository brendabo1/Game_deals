import re

async def extrair_preco(bloco):
    """
    Extrai preço e parcelas de um bloco de oferta
    """
    try:
        texto = await bloco.inner_text()
        texto = texto.replace("\n", " ").strip()

        # Valor monetário (R$ XXX,YY)
        match_valor = re.search(r"R\$\s?\d{1,3}(\.\d{3})*,\d{2}", texto)
        valor = match_valor.group(0) if match_valor else "-"

        # Parcelas (ex: 12x R$31,65) ou texto "cartão"
        match_parcelas = re.search(r"\d+x\s*R\$\s?\d{1,3}(\.\d{3})*,\d{2}", texto)
        if match_parcelas:
            parcelas = match_parcelas.group(0)
            parcelas = parcelas[2:]
        elif "cartão" in texto.lower():
            parcelas = "cartão"
        else:
            parcelas = "-"

        return valor, parcelas
    except:
        return "-", "-"
