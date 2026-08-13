from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimeStampedModel


class BackofficeLead(TimeStampedModel):
    __tablename__ = "backoffice_leads"

    name: Mapped[str] = mapped_column(String(120), default="Visitante")
    email: Mapped[str] = mapped_column(String(160), default="sem-email@lead.local", index=True)
    source_page: Mapped[str] = mapped_column(String(80), default="Liceu-Home")
    user_type: Mapped[str] = mapped_column(String(40), default="Guest")
    inferred_profile: Mapped[str] = mapped_column(String(40), index=True)
    intent: Mapped[str] = mapped_column(String(80))
    redirect_to: Mapped[str] = mapped_column(String(120))
    request_text: Mapped[str] = mapped_column(Text)
    thermometer_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(40), default="new")
    session_id: Mapped[str] = mapped_column(String(80), index=True)
