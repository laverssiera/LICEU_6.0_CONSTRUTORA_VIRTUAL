def analisar_sensores_unidade(id_unidade, dados_iot):
    """
    Monitora consumo de água e energia para prever vazamentos ou falhas.
    """
    alertas = []
    # Lógica de detecção de anomalia (Vazamento)
    if dados_iot['fluxo_agua'] > dados_iot['media_historica'] * 1.5:
        alertas.append({
            "tipo": "CRÍTICO",
            "msg": "Possível vazamento detectado. Fechamento automático sugerido.",
            "local_bim": "Banheiro_Suite_01"
        })
    
    return {
        "status_unidade": "ALERTA" if alertas else "SAUDÁVEL",
        "alertas": alertas,
        "proxima_manutencao": "2024-12-10" # Gerado pelo Plano 6D
    }
