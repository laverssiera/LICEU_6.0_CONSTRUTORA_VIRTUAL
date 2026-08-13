from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.schemas.business import BusinessCreate, BusinessResponse
from app.services.business_service import approve_business, create_business

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=BusinessResponse)
def create(data: BusinessCreate, db: Session = Depends(get_db)):
    return create_business(db, data)


@router.post("/{business_id}/approve", response_model=BusinessResponse)
async def approve(business_id: str, db: Session = Depends(get_db)):
    try:
        return await approve_business(db, business_id)
    except ValueError as exc:
        if str(exc) == "business_not_found":
            raise HTTPException(status_code=404, detail="Business not found") from exc
        raise
