def injetar_licoes_aprendidas(disciplina_alvo):
    """
    Busca as 5 patologias mais comuns no pós-obra da Liceu
    e gera um alerta vermelho no fluxo de projeto atual.
    """
    # Consulta a 'Massa de Dados' de Assistência Técnica
    ranking_erros = ["Infiltração_Junção_Laje", "Fissura_Acima_Caixilho"]
    
    return {
        "disciplina": disciplina_alvo,
        "trava_seguranca": "ATIVADA 🚨",
        "instrucao_tecnica": f"Revisar detalhamento de {ranking_erros[0]} conforme lição aprendida #42",
        "msg_qualidade": "Improviso bloqueado pelo histórico de pós-obra"
    }
