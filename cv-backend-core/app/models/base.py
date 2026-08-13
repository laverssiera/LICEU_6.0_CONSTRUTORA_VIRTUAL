from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Classe base para todos os modelos do sistema"""
    pass

class TimeStampedModel(Base):
    """Mixim para auditoria automática de tempo"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    # Garante a Honestidade: ninguém altera a data de criação
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # Registra a última atualização para controle de versão
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
