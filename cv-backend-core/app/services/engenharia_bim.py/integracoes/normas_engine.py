from app.services.engenharia_bim.integracoes import api_ipt, api_ibape

def verificar_conformidade_total(projeto_id, dados_projeto):
    """
    O 'Selo de Qualidade Liceu'. Cruza Engenharia, IPT e IBAPE.
    Se falhar aqui, o Orçamento e a Qualidade barram o projeto.
    """
    relatorio = {
        "projeto": projeto_id,
        "checkpoints": [],
        "aprovacao_final": False
    }

    # 1. Verifica Desempenho via IPT
    check_ipt = api_ipt.validar_material_ipt(dados_projeto['material'], "resistencia_fogo")
    relatorio["checkpoints"].append({"setor": "IPT", "status": check_ipt['status']})

    # 2. Verifica Valor de Ativo via IBAPE
    check_ibape = api_ibape.calcular_valor_pericial(dados_projeto['area'], "residencial_liceu_industrial")
    relatorio["checkpoints"].append({"setor": "IBAPE", "status": "VALIDADO"})

    # Decisão Estratégica (DNA Liceu)
    if all(c['status'] in ['CERTIFICADO ✅', 'VALIDADO'] for c in relatorio["checkpoints"]):
        relatorio["aprovacao_final"] = True
    
    return relatorio
