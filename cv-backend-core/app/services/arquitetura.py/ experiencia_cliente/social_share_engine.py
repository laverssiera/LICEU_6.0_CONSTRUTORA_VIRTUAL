def criar_sessao_colaborativa(id_projeto, lista_amigos_email):
    """
    Gera um link para os amigos votarem na cor da fachada ou no piso.
    Transforma o processo solitário em um evento social.
    """
    return {
        "url_game": f"https://liceu.io{id_projeto}",
        "modo": "VOTAÇÃO_COOPERATIVA",
        "ranking_amigos": "Quem der a melhor sugestão ganha brinde na inauguração",
        "integracao_whatsapp": True
    }
