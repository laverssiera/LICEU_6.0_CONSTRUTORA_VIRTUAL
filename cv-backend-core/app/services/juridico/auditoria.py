def calcular_compliance_spe(documentos_check: dict):
    """
    Calcula o score de 0 a 100 baseado na entrega de documentos técnicos e jurídicos.
    Pesos baseados na criticidade para formação da SPE e Patrimônio de Afetação.
    """
    # Definição de pesos para o DNA Liceu 6.0
    pesos = {
        "matricula_atualizada": 30,          # Fundamental para propriedade
        "certidao_negativa_debitos": 20,     # Risco de penhora/bloqueio
        "projeto_aprovado_prefeitura": 20,   # Viabilidade técnica legal
        "registro_memorial_incorporacao": 15, # Base para o Patrimônio de Afetação
        "contrato_arbitragem_assinado": 15    # Segurança jurídica extrajudicial
    }
    
    score_total = 0
    pendencias = []
    
    # Valida o que foi entregue (True) e o que falta (False/None)
    for doc, peso in pesos.items():
        if documentos_check.get(doc) is True:
            score_total += peso
        else:
            # Formata o nome para exibição no Frontend
            nome_amigavel = doc.replace("_", " ").title()
            pendencias.append(nome_amigavel)
            
    return {
        "score": score_total,
        "aprovado": score_total == 100,
        "pendencias": pendencias,
        "mensagem": "Documentação 100% Auditada" if score_total == 100 else "Diligências Pendentes"
    }

