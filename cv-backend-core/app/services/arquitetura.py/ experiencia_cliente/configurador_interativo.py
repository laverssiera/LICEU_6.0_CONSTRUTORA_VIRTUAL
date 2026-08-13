def gerar_link_compartilhamento(id_projeto, token_amigo):
    """
    Cria um link seguro para o amigo entrar no Vue.js e 'votar' nos acabamentos.
    """
    return {
        "url_interativa": f"https://liceu.io{id_projeto}/guest",
        "permissoes": ["comentar", "votar_cor", "visualizar_3d"],
        "gamificacao": "Amigo ganha desconto de 5% se o cliente fechar a obra"
    }
