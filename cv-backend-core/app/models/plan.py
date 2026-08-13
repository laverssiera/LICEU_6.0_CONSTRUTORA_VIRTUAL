from sqlalchemy import Column, ForeignKey, Integer, String, Text

from app.models.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(80), nullable=False, default="liceu", index=True)
    initiative_id = Column(Integer, ForeignKey("initiatives.id"), nullable=False, index=True)
    title = Column(String(180), nullable=False)
    description = Column(Text, nullable=False, default="")
    status = Column(String(30), nullable=False, default="backlog", index=True)
    priority = Column(String(30), nullable=False, default="normal", index=True)