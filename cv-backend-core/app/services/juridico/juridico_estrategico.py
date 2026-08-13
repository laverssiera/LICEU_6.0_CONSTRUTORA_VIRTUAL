def analisar_impacto_processo(valor_acao, tempo_medio_juiz, custo_obra_parada_dia):
    """
    Calcula se a briga jurídica fere o Planejamento Estratégico do Liceu.
    """
    custo_juridico_estimado = valor_acao * 0.20 # Honorários e Custas
    perda_financeira_tempo = tempo_medio_juiz * custo_obra_m2 # Impacto no VGV
    
    # Se o custo de brigar for maior que 30% do lucro da SPE, o sistema sugere ACORDO
    if (custo_juridico_estimado + perda_financeira_tempo) > (lucro_spe * 0.3):
        return {
            "estrategia": "ACORDO IMEDIATO",
            "motivo": "Preservação do Fluxo de Caixa da SPE",
            "valor_max_acordo": valor_acao * 0.7
        }
    return {"estrategia": "DEFESA AGRESSIVA", "motivo": "Tese jurídica sólida com baixo risco financeiro"}
