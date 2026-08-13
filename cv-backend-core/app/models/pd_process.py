from sqlalchemy import Column, ForeignKey, Integer, String, Text

from app.models.base import Base


class PDProcess(Base):
    __tablename__ = "pd_processes"

    id = Column(Integer, primary_key=True, index=True)
    initiative_id = Column(Integer, ForeignKey("initiatives.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    process_code = Column(String(120), nullable=False, index=True)
    title = Column(String(180), nullable=False)
    description = Column(Text, nullable=False, default="")
    process_type = Column(String(30), nullable=False, default="research", index=True)
    target_monolith = Column(String(30), nullable=False, default="pdi_ia", index=True)
    status = Column(String(30), nullable=False, default="draft", index=True)