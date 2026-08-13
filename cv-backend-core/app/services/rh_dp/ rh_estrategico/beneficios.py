def listar_clube_vantagens(id_colaborador):
    """
    Exibe os convênios disponíveis baseados na localização do colaborador.
    """
    convenios = {
        "saude": "Plano Global para PJs com desconto de grupo",
        "educacao": "Acesso Premium à Escola da Irmandade (100% Grátis)",
        "lazer": "Clube de Vantagens em Parques e Academias (Gympass)"
    }
    
    return {
        "meus_beneficios": convenios,
        "voucher_ativo": f"LICEU-PRO-2026-{id_colaborador}",
        "msg": "Aproveite seu tempo de descanso. A Irmandade cuida de você."
    }
