def capturar_lead_social(dados_amigo, projeto_referencia_id):
    """
    Transforma o 'voto' do amigo em um Lead qualificado no banco de dados.
    Analisa o que o amigo mais gostou no projeto do cliente original.
    """
    score_interesse = calcular_score_lead(dados_amigo) # Baseado no tempo de navegação no game
    
    return {
        "status": "LEAD_QUALIFICADO_SOCIAL",
        "email": dados_amigo['email'],
        "interesse_principal": dados_amigo['item_votado'], # Ex: 'Piscina_Industrial'
        "origem": f"Indicação_Projeto_{projeto_referencia_id}",
        "proxima_acao": "Enviar cupom de desconto para Estudo de Viabilidade"
    }

def calcular_score_lead(dados):
    # Lógica simples: se o amigo comentou ou votou em mais de 3 itens, o score é ALTO
    return 85 if len(dados.get('interacoes', [])) > 3 else 40
