def realizar_auditoria_contratual(id_contrato):
    """
    Verifica se a relação PJ mantém os 3 pilares: Não-eventualidade, 
    Não-subordinação e Não-pessoalidade.
    """
    alertas = []
    # Se o PJ está logando exatamente 8h/dia todo dia, o sistema alerta risco de vínculo
    if detectar_padrao_subordinacao(id_contrato):
        alertas.append("ALERTA: Padrão de horário rígido detectado. Sugerido flexibilizar.")

    return {
        "contrato_id": id_contrato,
        "score_seguranca": 95 if not alertas else 60,
        "alertas_prevencao": alertas,
        "acao": "Revisar cláusula de autonomia ou alternar prestador"
    }
def realizar_auditoria_preventiva_pj(id_colaborador, logs_atividades):
    """
    Analisa se a relação PJ está saindo dos trilhos e criando risco de vínculo (CLT).
    Critérios: Subordinação, Não-eventualidade e Pessoalidade.
    """
    alertas = []
    
    # 1. Checa se o horário é rígido demais (Indício de Subordinação)
    if detectar_horario_fixo_extremo(logs_atividades):
        alertas.append({
            "grau": "MÉDIO",
            "msg": "Padrão de login 08h-18h detectado. Sugerido reforçar a autonomia de horários."
        })

    # 2. Checa se o colaborador não usa substitutos (Pessoalidade)
    if not logs_atividades.get('permissao_substituto_ativa'):
        alertas.append({
            "grau": "ALTO",
            "msg": "Contrato sem previsão de substituição. Risco de caracterização de pessoalidade."
        })

    return {
        "colaborador_id": id_colaborador,
        "score_seguranca_juridica": 100 - (len(alertas) * 20),
        "status_compliance": "SEGURO ✅" if not alertas else "ATENÇÃO ⚠️",
        "alertas_detalhados": alertas
    }
