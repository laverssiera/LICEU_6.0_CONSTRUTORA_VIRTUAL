def registrar_ocorrencia_pos_obra(id_unidade, patologia_detectada):
    """
    Alimenta o Planejamento Estratégico com custos inesperados.
    Se houve infiltração, o Orçamento de 'impermeabilizacao.py' é ajustado.
    """
    custo_reparo = calcular_reparo(patologia_detectada)
    
    return {
        "impacto_financeiro": custo_reparo,
        "feedback_engenharia": "AJUSTAR_DETALHE_X_NO_BIM",
        "procedimento_reparo": "POP_ASSISTENCIA_04",
        "perda_de_margem_spe": f"{round((custo_reparo/100000)*100, 2)}%"
    }
