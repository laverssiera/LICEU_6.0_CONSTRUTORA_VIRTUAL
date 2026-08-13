import numpy_financial as npf

def calcular_viabilidade_financeira(
    area_construida_estimada: float,
    valor_venda_m2: float,
    custo_obra_m2: float,
    valor_terreno: float,
    prazo_meses: int = 12
):
    """
    Calcula os indicadores do Liceu 6.0 para o investidor.
    """
    # 1. VGV (Valor Geral de Vendas)
    # Área vendável costuma ser ~90% da construída em sistemas pré-moldados
    area_vendavel = area_construida_estimada * 0.9
    vgv = area_vendavel * valor_venda_m2

    # 2. Custos (DNA Liceu)
    custo_total_obra = area_construida_estimada * custo_obra_m2
    taxa_plataforma = vgv * 0.05  # 5% de taxa de ecossistema
    
    custo_total_projeto = valor_terreno + custo_total_obra + taxa_plataforma
    
    # 3. Lucro Líquido Estimado
    lucro_estimado = vgv - custo_total_projeto
    margem_lucro = (lucro_estimado / vgv) * 100

    # 4. ROI (Retorno sobre Investimento)
    roi = (lucro_estimado / custo_total_projeto) * 100

    # 5. TIR (Taxa Interna de Retorno) - Simplificada para o período
    # Fluxo: [Investimento Negativo, 0, 0, ..., Recebimento VGV]
    fluxo_caixa = [-custo_total_projeto] + [0] * (prazo_meses - 1) + [vgv]
    tir_mensal = npf.irr(fluxo_caixa)
    tir_anual = ((1 + tir_mensal) ** 12) - 1

    # 6. Classificação Liceu
    if tir_anual > 0.20: # Exemplo: Viável se > 20% ao ano
        classificacao = "VIÁVEL ✅"
    elif tir_anual > 0.12:
        classificacao = "MARGINAL ⚠️"
    else:
        classificacao = "INVIÁVEL ❌"

    return {
        "vgv": round(vgv, 2),
        "investimento_total": round(custo_total_projeto, 2),
        "lucro_estimado": round(lucro_estimado, 2),
        "roi": f"{round(roi, 2)}%",
        "tir_anual": f"{round(tir_anual * 100, 2)}%",
        "classificacao": classificacao,
        "payback_meses": prazo_meses
    }
def identificar_ponto_critico(dados_projeto):
    riscos = []
    
    # Risco Financeiro: Sensibilidade de Preço
    if dados_projeto['margem_lucro'] < 15:
        riscos.append({
            "tipo": "FINANCEIRO",
            "fator": "Margem Estreita",
            "detalhe": "Variação de 5% no custo industrial inviabiliza o ROI do investidor."
        })

    # Risco Técnico: Solo/Topografia (Exemplo de entrada de dados)
    if dados_projeto.get('topografia_declive', 0) > 20:
        riscos.append({
            "tipo": "TÉCNICO",
            "fator": "Movimentação de Terra",
            "detalhe": "Declividade alta exige muros de arrimo, elevando custo de fundação em 30%."
        })

    # Risco Social/Legal: Zoneamento
    if dados_projeto['zoneamento'] == "ZEIS":
        riscos.append({
            "tipo": "SOCIAL/LEGAL",
            "fator": "Cota de Solidariedade",
            "detalhe": "Exigência de unidades de baixa renda pode reduzir o VGV final."
        })

    return riscos # Isso vira o "Ponto Crítico" no Relatório
