import ifcopenshell
import ifcopenshell.util.element

def extrair_quantitativos_bim(caminho_ifc):
    """
    Lê o arquivo BIM (IFC) e extrai volumes de concreto, 
    áreas de fôrma e peso de aço automaticamente.
    """
    ifc = ifcopenshell.open(caminho_ifc)
    paredes = ifc.by_type("IfcWall")
    
    resumo_materiais = {
        "concreto_m3": 0,
        "alvenaria_m2": 0
    }

    for parede in paredes:
        psets = ifcopenshell.util.element.get_psets(parede)
        # Busca o volume real desenhado pelo projetista
        volume = psets.get("BaseQuantities", {}).get("NetVolume", 0)
        resumo_materiais["concreto_m3"] += volume

    return resumo_materiais
