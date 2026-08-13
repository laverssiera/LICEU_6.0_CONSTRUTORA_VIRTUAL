from uuid import UUID

from sqlalchemy.orm import Session

from app.core.nats import publish
from app.models.business import BusinessPipeline
from app.schemas.business import BusinessCreate


def create_business(db: Session, data: BusinessCreate) -> BusinessPipeline:
    business = BusinessPipeline(**data.model_dump())
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


async def approve_business(db: Session, business_id: str) -> BusinessPipeline:
    business = db.get(BusinessPipeline, UUID(business_id))
    if business is None:
        raise ValueError("business_not_found")

    business.stage = "Aprovado"
    db.add(business)
    db.commit()
    db.refresh(business)

    await publish(
        "business.approved",
        {
            "business_id": str(business.id),
            "title": business.title,
            "portfolio": business.portfolio,
            "program": business.program,
        },
    )

    return business
