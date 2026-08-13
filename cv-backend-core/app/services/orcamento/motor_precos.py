def precificar_projeto(quantitativos, margem_estrategica):
    """
    Cruza o quantitativo BIM com a tabela de custos Liceu + Mercado.
    """
    # Exemplo de custos dinâmicos (Poderiam vir de uma API)
    custos_unitarios = {
        "concreto_m3": 550.00, # Custo industrial Liceu
        "mao_de_obra_m2": 120.00
    }
    
    custo_direto = quantitativos["concreto_m3"] * custos_unitarios["concreto_m3"]
    
    # Aplica o BDI (Benefícios e Despesas Indiretas) definido pelo Planejamento
    preco_final = custo_direto * (1 + margem_estrategica)
    
    return {
        "custo_industrial_liceu": round(custo_direto, 2),
        "preco_venda_sugerido": round(preco_final, 2),
        "markup_aplicado": f"{margem_estrategica * 100}%"
    }
