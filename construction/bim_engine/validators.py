def validate_wall_params(params):
    # Exemplo simples de validação
    if params.get("thickness", 0) <= 0:
        raise ValueError("Espessura inválida")
    if params.get("height", 0) <= 0:
        raise ValueError("Altura inválida")
    return True
