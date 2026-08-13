from fastapi import FastAPI

from app.core.db import Base, engine
from app.core.nats import connect_nats
from app.routes import business

app = FastAPI(title="Liceu Backend")

app.include_router(business.router, prefix="/business", tags=["business"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "backend"}


@app.on_event("startup")
async def startup() -> None:
    # Mantem compatibilidade para ambientes sem Alembic aplicado.
    Base.metadata.create_all(bind=engine)
    await connect_nats()
