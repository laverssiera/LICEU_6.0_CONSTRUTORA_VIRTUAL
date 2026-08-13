# orcamento/analise_estratégica.py

def validar_orcamento_diretoria(orcamento_final, meta_lucro_minima=0.15):
    """
    Verifica se o orçamento está alinhado com o Planejamento Estratégico.
    """
    lucro_estimado = (orcamento_final['preco_venda_sugerido'] - orcamento_final['custo_industrial_liceu']) / orcamento_final['preco_venda_sugerido']
    
    if lucro_estimado >= meta_lucro_minima:
        return {"status": "APROVADO ✅", "acao": "Liberar para Comercial"}
    else:
        return {
            "status": "REVISAR ⚠️", 
            "acao": "Reduzir desperdício via Kit Liceu ou renegociar insumos",
            "gap_lucro": f"{round((meta_lucro_minima - lucro_estimado)*100, 2)}%"
        }
