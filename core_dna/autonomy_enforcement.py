class AutonomyViolation(Exception):
    """Exceção lançada quando um John tenta executar ação acima do seu nível de autonomia."""
    pass

def enforce_autonomy(john, action):
    """
    Middleware obrigatório: bloqueia execução acima do nível de autonomia do John.
    john: objeto ou dict com atributo 'autonomy_level'
    action: objeto ou dict com atributo 'level' (AutonomyLevel)
    """
    john_level = getattr(john, 'autonomy_level', None) or john.get('autonomy_level')
    action_level = getattr(action, 'level', None) or action.get('level')
    if action_level is None or john_level is None:
        raise ValueError("john.autonomy_level e action.level são obrigatórios")
    if action_level > john_level:
        raise AutonomyViolation(f"Ação {action_level} acima do permitido para {john_level}")
    return True
