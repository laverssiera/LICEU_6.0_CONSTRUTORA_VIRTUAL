def monitorar_vida_util_forma(id_forma, total_usos):
    """Controla o desgaste das formas metálicas para evitar peças fora do prumo."""
    limite_usos = 500
    if total_usos >= limite_usos:
        return {"status": "MANUTENÇÃO_NECESSÁRIA", "acao": "Retificar_Faces"}
    return {"vida_remanescente": f"{limite_usos - total_usos} ciclos"}

