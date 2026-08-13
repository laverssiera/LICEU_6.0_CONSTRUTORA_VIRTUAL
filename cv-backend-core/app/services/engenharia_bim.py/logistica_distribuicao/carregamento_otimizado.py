def planejar_ordem_carregamento(id_projeto, lista_kits):
    """
    Define a ordem de carregamento baseada na sequência de montagem (BIM 4D).
    Regra: O que monta primeiro fica na porta do caminhão.
    """
    # Ordena os kits pela sequência cronológica de montagem
    kits_ordenados = sorted(lista_kits, key=lambda x: x['ordem_montagem'])
    
    # Inverte para o carregamento (Last In, First Out)
    plano_carga = kits_ordenados[::-1] 
    
    return {
        "projeto": id_projeto,
        "total_volumes": len(plano_carga),
        "sequencia_estiva": [k['id_kit'] for k in plano_carga],
        "centro_gravidade": "ESTÁVEL",
        "msg": "Plano de carga gerado para conferência via App"
    }
