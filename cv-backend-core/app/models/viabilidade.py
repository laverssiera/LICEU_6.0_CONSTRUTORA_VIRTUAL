from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class EstudoViabilidade(Base):
    __tablename__ = "estudos_viabilidade"

    id = Column(Integer, primary_key=True, index=True)
    endereco = Column(String, nullable=False)
    area_terreno = Column(Float, nullable=False)
    valor_terreno = Column(Float, nullable=False)
    matricula = Column(String, nullable=False)
    valor_venda_m2 = Column(Float, default=4500)
    custo_obra_m2 = Column(Float, default=2200)
    zona_detectada = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())