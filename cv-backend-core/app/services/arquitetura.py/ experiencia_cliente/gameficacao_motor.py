def processar_escolha_gamificada(id_projeto, item_selecionado, saldo_pontos):
    """
    Transforma a seleção de materiais em um jogo.
    Se o cliente escolhe um item 'Eco-Friendly', ganha pontos de Sustentabilidade.
    """
    recompensas = {
        "painel_solar": {"pontos": 500, "badge": "Eco-Warrior", "desconto_taxa": 0.02},
        "automacao_premium": {"pontos": 300, "badge": "Tech-Master", "fator_uau": True},
        "reuso_agua": {"pontos": 400, "badge": "Water-Saver", "nps_potencial": +10}
    }

    premio = recompensas.get(item_selecionado, {"pontos": 10, "badge": "Novato"})
    
    return {
        "status": "CONQUISTA DESBLOQUEADA! 🏆",
        "badge": premio['badge'],
        "novos_pontos": saldo_pontos + premio['pontos'],
        "efeito_visual_vue": "confetes_digitais",
        "mensagem_nps": "Você acaba de valorizar seu imóvel em 5% com essa escolha!"
    }
