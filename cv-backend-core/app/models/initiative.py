from sqlalchemy import Column, ForeignKey, Integer, String, Text

from app.models.base import Base


class Initiative(Base):
    __tablename__ = "initiatives"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(80), nullable=False, default="liceu", index=True)
    objective_id = Column(Integer, ForeignKey("objectives.id"), nullable=False, index=True)
    name = Column(String(180), nullable=False)
    description = Column(Text, nullable=False, default="")
    initiative_type = Column(String(30), nullable=False, index=True)
    owner = Column(String(120), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="backlog", index=True)