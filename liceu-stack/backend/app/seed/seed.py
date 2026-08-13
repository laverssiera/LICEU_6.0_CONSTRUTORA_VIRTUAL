from app.core.db import SessionLocal
from app.models.business import BusinessPipeline


def run() -> None:
    db = SessionLocal()
    try:
        existing = db.query(BusinessPipeline).filter(BusinessPipeline.title == "Empreendimento 20 casas").first()
        if existing is not None:
            print("Seed ja executado")
            return

        sample = BusinessPipeline(
            title="Empreendimento 20 casas",
            portfolio="Obras Comuns",
            program="Residencial",
            stage="Ideia",
            estimated_cost=2000000,
            expected_return=3200000,
        )

        db.add(sample)
        db.commit()
        print("Seed executado")
    finally:
        db.close()


if __name__ == "__main__":
    run()
