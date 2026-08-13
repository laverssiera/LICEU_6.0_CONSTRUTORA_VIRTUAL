def agendar_atividade_grupo(tipo_evento):
    """
    Organiza Happy Hours virtuais, Hackathons de Engenharia ou Treinos Esportivos.
    """
    formatos = {
        "VIRTUAL": "Café com o Diretor (Via Plataforma)",
        "PRESENCIAL": "Churrasco de Conclusão de SPE (No Galpão)",
        "TREINAMENTO": "Workshop: Inovações BIM 7D"
    }
    
    return {
        "evento": formatos.get(tipo_evento),
        "data": "Última sexta-feira do mês",
        "confirmacao_presenca_vue": "Botão habilitado no Dashboard do Colaborador"
    }
