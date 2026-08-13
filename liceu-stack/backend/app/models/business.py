import uuid
from datetime import datetime

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class BusinessPipeline(Base):
    __tablename__ = "business_pipeline"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    portfolio: Mapped[str] = mapped_column(String(120), nullable=False)
    program: Mapped[str] = mapped_column(String(120), nullable=False)
    stage: Mapped[str] = mapped_column(String(40), nullable=False, default="Ideia")
    estimated_cost: Mapped[float] = mapped_column(Numeric, nullable=False)
    expected_return: Mapped[float] = mapped_column(Numeric, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
