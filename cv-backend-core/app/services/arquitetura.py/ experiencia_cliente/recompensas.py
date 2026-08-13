class SistemaRecompensas:
    def __init__(self, db):
        self.db = db

    def processar_ganho_pontos(self, usuario_id, acao):
        """
        Atribui pontos baseados no comportamento estratégico.
        """
        regras = {
            "INDICACAO_CONVERTIDA": 5000, # Amigo virou lead qualificado
            "COMPARTILHAR_RA": 500,       # Postou foto da casa em RA no Instagram
            "VOTO_COLETIVO_CONCLUIDO": 300, # Finalizou a rodada de votos com amigos
            "ESCOLHA_SUSTENTAVEL": 1000   # Optou por Painel Solar ou Reuso de Água
        }
        
        pontos = regras.get(acao, 100)
        # Salva no banco de dados do usuário
        return {"id_usuario": usuario_id, "pontos_ganhos": pontos, "novo_saldo": 6800}

    def resgatar_beneficio(self, usuario_id, pontos_necessarios, premio_tipo):
        """
        Troca pontos por upgrades reais na obra Liceu.
        """
        # Ex: Trocar 5000 pontos por fechadura biométrica grátis
        return {
            "status": "RESGATE_APROVADO",
            "premio": premio_tipo,
            "vouch_digital": f"LICEU-REWARD-{usuario_id}"
        }
