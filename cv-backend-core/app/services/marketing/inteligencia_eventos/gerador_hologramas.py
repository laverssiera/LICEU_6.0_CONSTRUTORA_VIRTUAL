def preparar_holograma_amigao(id_evento, animacao_tipo="SAUDACAO"):
    """
    Gera o arquivo de vídeo/3D otimizado para projetores holográficos.
    Animacoes: SAUDACAO, EXPLICANDO_BIM, CONVIDANDO_ESCOLA.
    """
    assets = {
        "SAUDACAO": "amigao_holograma_wave.mp4",
        "EXPLICANDO_BIM": "amigao_holograma_bim_explainer.mp4"
    }
    
    return {
        "status": "HOLOGRMA_PRONTO_PARA_STREAM",
        "file_url": f"https://api.liceu.io{assets[animacao_tipo]}",
        "interatividade": "Habilitar Microfone para Resposta em Tempo Real"
    }

