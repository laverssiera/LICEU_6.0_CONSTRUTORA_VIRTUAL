from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.models.base import Base


class Objective(Base):
    __tablename__ = "objectives"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(80), nullable=False, default="liceu", index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    metric = Column(String(180), nullable=False)
    target = Column(Float, nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(30), nullable=False, default="backlog", index=True)