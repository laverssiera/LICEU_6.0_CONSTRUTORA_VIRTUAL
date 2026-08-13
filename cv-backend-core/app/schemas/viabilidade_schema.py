from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EstudoViabilidadeCreate(BaseModel):
    endereco: str
    area_terreno: float
    valor_terreno: float
    matricula: str
    valor_venda_m2: Optional[float] = 4500
    custo_obra_m2: Optional[float] = 2200


class EstudoViabilidadeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    endereco: str
    area_terreno: float
    valor_terreno: float
    matricula: str
    valor_venda_m2: float
    custo_obra_m2: float
    zona_detectada: Optional[str]
    created_at: datetime


class EstatisticasResponse(BaseModel):
    vgv_total_mapeado: int = 0
    total_analises: int = 0
    taxa_viabilidade: str = "0%"