class AmigaoLiceu:
    """
    IA Consultora: Ajuda na obra, tira dúvidas de BIM e indica a Escola.
    """
    def responder_usuario(self, pergunta, perfil_usuario):
        # 1. Identifica a intenção (Dúvida Técnica, Compra ou Estudo)
        if "fissura" in pergunta.lower() or "rachadura" in pergunta.lower():
            return {
                "resposta": "Opa! Fissura pode ser sério. Tira uma foto e me manda aqui? Vou rodar meu scanner YOLO11 para te dar um laudo preliminar agora!",
                "cta": "ABRIR_CAMERA_IA",
                "setor": "Patologias"
            }
        
        if "aprender" in pergunta.lower() or "trabalhar" in pergunta.lower():
            return {
                "resposta": "Quer virar um Irmão Montador? Nossa Escola tem cursos gratuitos de BIM e Montagem Industrial. Vamos mudar sua carreira?",
                "cta": "ABRIR_INSCRICAO_ESCOLA",
                "setor": "Educação"
            }

        return {
            "resposta": "Eu sou o Amigão Liceu! Posso calcular a viabilidade do seu terreno ou te mostrar como a gente economiza 28% na sua obra. O que quer ver primeiro?",
            "cta": "MOSTRAR_DASHBOARD_EVTL",
            "setor": "Marketing"
        }
