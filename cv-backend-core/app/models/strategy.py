from sqlalchemy import Column, Integer, String, Text

from app.models.base import Base


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(80), nullable=False, default="liceu", index=True)
    name = Column(String(180), nullable=False, index=True)
    description = Column(Text, nullable=False, default="")
    priority = Column(String(30), nullable=False, default="normal", index=True)
    status = Column(String(30), nullable=False, default="backlog", index=True)