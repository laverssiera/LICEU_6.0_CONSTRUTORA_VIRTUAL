from __future__ import annotations

import requests
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="Liceu6.0_App_Vistoria")


def detectar_zona_urbanistica(endereco: str) -> str:
    endereco_normalizado = endereco.lower()
    if "paulista" in endereco_normalizado:
        return "ZEU"
    if "vila" in endereco_normalizado:
        return "ZM"
    return "ZONA_RESIDENCIAL"


def buscar_coordenadas_gratuito(cep_ou_endereco: str):
    try:
        local = geolocator.geocode(f"{cep_ou_endereco}, Brasil", timeout=10)
        if local:
            return {"lat": local.latitude, "lng": local.longitude}
        return None
    except Exception:
        return None


def consultar_zoneamento_geosampa(lat: float, lng: float):
    url_wfs = "https://geosampa.prefeitura.sp.gov.br"
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": "geosampa:camada_zoneamento",
        "outputFormat": "application/json",
        "cql_filter": f"CONTAINS(geom, POINT({lng} {lat}))",
    }

    try:
        response = requests.get(url_wfs, params=params, timeout=15)
        dados = response.json()
        if dados.get("features"):
            propriedades = dados["features"][0]["properties"]
            return propriedades.get("sigla_zona", "ZONA_DESCONHECIDA")
        return "FORA_DE_SP_OU_ZONA_NAO_MAPEADA"
    except Exception:
        return "ERRO_CONEXAO_PREFEITURA"


def processar_estudo_urbanistico(endereco: str, area_terreno: float):
    coords = buscar_coordenadas_gratuito(endereco)
    if not coords:
        return {"erro": "Endereço não localizado"}

    zona = consultar_zoneamento_geosampa(coords["lat"], coords["lng"])
    parametros = {
        "ZEU": 4.0,
        "ZM": 2.0,
        "ZCOR": 1.0,
        "ZUCA": 1.0,
    }
    ca = parametros.get(zona, 1.0)

    return {
        "latitude": coords["lat"],
        "longitude": coords["lng"],
        "zona": zona,
        "ca_aplicado": ca,
        "potencial_construtivo": area_terreno * ca,
    }
