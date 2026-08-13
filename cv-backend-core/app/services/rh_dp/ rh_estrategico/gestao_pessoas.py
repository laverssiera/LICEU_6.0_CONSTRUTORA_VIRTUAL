from datetime import datetime

def disparar_ritual_integracao(id_colaborador, nome_colaborador):
    """
    Inicia a jornada do novo 'Irmão'. Envia vídeos e agenda o onboarding.
    """
    videos_institucionais = [
        {"titulo": "A Visão Liceu 6.0", "url": "https://liceu.io"},
        {"titulo": "O DNA da Industrialização", "url": "https://liceu.io"}
    ]
    
    return {
        "status": "INTEGRAÇÃO_INICIADA",
        "boas_vindas": f"Bem-vindo à Irmandade, {nome_colaborador}!",
        "playlist_treinamento": videos_institucionais,
        "primeira_tarefa": "Assistir ao Manifesto e realizar o Quiz Cultural"
    }

def verificar_datas_importantes(db_colaboradores):
    """
    Varre o banco em busca de aniversários e tempo de casa.
    Gera lembretes para o Amigão Liceu parabenizar no Slack/WhatsApp.
    """
    hoje = datetime.now().strftime("%d/%m")
    eventos = []
    
    for c in db_colaboradores:
        if c.data_nascimento.strftime("%d/%m") == hoje:
            eventos.append({"tipo": "ANIVERSÁRIO", "nome": c.nome, "msg": "Parabéns, Irmão!"})
            
    return eventos
