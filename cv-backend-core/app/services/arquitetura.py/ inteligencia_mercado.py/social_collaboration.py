def gerar_sessao_votacao(id_projeto, id_cliente):
    """
    Cria um link gamificado onde amigos dão notas de 1 a 5 para escolhas do cliente.
    """
    token_sessao = f"VOTE-{id_projeto}-SOCIAL"
    
    return {
        "link_compartilhamento": f"https://liceu.io{token_sessao}",
        "itens_em_votacao": ["Cor da Fachada", "Tipo de Piso", "Kit Automação"],
        "recompensa_amigo": "Ganhe 5% de desconto na sua futura análise de terreno ao votar!",
        "captura_lead": True # O sistema pedirá o e-mail do amigo para validar o voto
    }

def processar_voto_amigo(id_projeto, lead_data, voto):
    """
    Registra o voto e salva o amigo como um 'Lead de Indicação' no banco de dados.
    """
    # Salva no banco: Nome, E-mail e o que ele mais gostou no projeto do amigo
    print(f"Novo Lead: {lead_data['email']} interessado em {voto['item_preferido']}")
    
    return {"status": "Voto Computado!", "xp_ganho_pelo_cliente": 100}
