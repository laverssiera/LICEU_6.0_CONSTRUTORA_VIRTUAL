from sqlalchemy import Column, ForeignKey, Integer, String, Text

from app.models.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(80), nullable=False, default="liceu", index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False, index=True)
    title = Column(String(180), nullable=False)
    description = Column(Text, nullable=False, default="")
    assigned_to = Column(String(120), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="backlog", index=True)
    priority = Column(String(30), nullable=False, default="normal", index=True)