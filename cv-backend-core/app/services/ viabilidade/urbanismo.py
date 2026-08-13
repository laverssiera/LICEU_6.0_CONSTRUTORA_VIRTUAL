# app/services/viabilidade/urbanismo.py

# from geopy.geocoders import Nominatim
import requests
import time

# Inicializa o Geocodificador Gratuito (OSM)
# Importante: O Nominatim exige um 'user_agent' único (coloque o nome do seu app)
geolocator = Nominatim(user_agent="Liceu6.0_App_Vistoria")

def detectar_zona_urbanistica(endereco: str) -> str:
    """
    Detecta a zona urbanística baseada no endereço.
    """
    # Simulação simples para teste
    if "paulista" in endereco.lower():
        return "ZEU"
    elif "vila" in endereco.lower():
        return "ZM"
    else:
        return "ZONA_RESIDENCIAL"

def buscar_coordenadas_gratuito(cep_ou_endereco: str):

def buscar_coordenadas_gratuito(cep_ou_endereco: str):
    """
    Converte CEP/Endereço em Lat/Lng usando OpenStreetMap (Gratis)
    """
    try:
        # Adicionamos ", Brasil" para garantir que a busca foque aqui
        local = geolocator.geocode(f"{cep_ou_endereco}, Brasil", timeout=10)
        if local:
            return {"lat": local.latitude, "lng": local.longitude}
        return None
    except Exception as e:
        print(f"Erro no OpenStreetMap: {e}")
        return None

def consultar_zoneamento_geosampa(lat: float, lng: float):
    """
    Consulta o GeoSampa (Prefeitura SP) via WFS
    """
    url_wfs = "https://geosampa.prefeitura.sp.gov.br"
    
    # Filtro espacial: busca a zona que CONTÉM o ponto (lat, lng)
    # O GeoSampa usa a ordem (lng lat) no filtro WFS
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": "geosampa:camada_zoneamento",
        "outputFormat": "application/json",
        "cql_filter": f"CONTAINS(geom, POINT({lng} {lat}))"
    }
    
    try:
        response = requests.get(url_wfs, params=params, timeout=15)
        dados = response.json()
        
        if dados.get("features") and len(dados["features"]) > 0:
            # Pega a sigla da zona (Ex: ZEU, ZM)
            propriedades = dados["features"][0]["properties"]
            return propriedades.get("sigla_zona", "ZONA_DESCONHECIDA")
        return "FORA_DE_SP_OU_ZONA_NAO_MAPEADA"
    except Exception as e:
        print(f"Erro ao conectar no GeoSampa: {e}")
        return "ERRO_CONEXAO_PREFEITURA"

def processar_estudo_urbanistico(endereco: str, area_terreno: float):
    """
    Orquestrador: Endereço -> Coordenada -> Zona -> Potencial
    """
    # 1. Pega coordenadas (Gratis)
    coords = buscar_coordenadas_gratuito(endereco)
    if not coords:
        return {"erro": "Endereço não localizado"}

    # 2. Busca Zona na Prefeitura
    zona = consultar_zoneamento_geosampa(coords['lat'], coords['lng'])
    
    # 3. Define parâmetros (CA/TO) simplificados para o teste
    parametros = {
        "ZEU": 4.0, "ZM": 2.0, "ZCOR": 1.0, "Zuca": 1.0
    }
    ca = parametros.get(zona, 1.0) # Se não achar, assume CA 1.0 (segurança)
    
    return {
        "latitude": coords['lat'],
        "longitude": coords['lng'],
        "zona": zona,
        "ca_aplicado": ca,
        "potencial_construtivo": area_terreno * ca
    }
