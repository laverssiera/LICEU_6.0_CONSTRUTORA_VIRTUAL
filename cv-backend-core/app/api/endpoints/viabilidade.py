from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.viabilidade import EstudoViabilidade
from app.schemas.viabilidade_schema import (
    EstudoViabilidadeCreate,
    EstudoViabilidadeResponse,
    EstatisticasResponse
)
from app.services.viabilidade.financeiro import calcular_viabilidade_financeira
from app.services.viabilidade.urbanismo import detectar_zona_urbanistica
import random

router = APIRouter()

@router.get("/estatisticas/", response_model=EstatisticasResponse)
def get_estatisticas(db: Session = Depends(get_db)):
    total_analises = db.query(EstudoViabilidade).count()
    # Simulação de VGV
    vgv_total = total_analises * 1000000  # Exemplo
    taxa = f"{random.randint(70, 95)}%"  # Simulação
    return EstatisticasResponse(
        vgv_total_mapeado=vgv_total,
        total_analises=total_analises,
        taxa_viabilidade=taxa
    )

@router.get("/listar-estudos/", response_model=list[EstudoViabilidadeResponse])
def listar_estudos(db: Session = Depends(get_db)):
    return db.query(EstudoViabilidade).all()

@router.post("/gerar-evtl/", response_model=EstudoViabilidadeResponse)
def gerar_estudo_viabilidade(estudo: EstudoViabilidadeCreate, db: Session = Depends(get_db)):
    try:
        # Detectar zona urbanística
        zona = detectar_zona_urbanistica(estudo.endereco)
        
        # Calcular viabilidade financeira
        viabilidade = calcular_viabilidade_financeira(
            estudo.area_terreno,
            estudo.valor_terreno,
            estudo.valor_venda_m2,
            estudo.custo_obra_m2
        )
        
        # Criar estudo
        novo_estudo = EstudoViabilidade(
            endereco=estudo.endereco,
            area_terreno=estudo.area_terreno,
            valor_terreno=estudo.valor_terreno,
            matricula=estudo.matricula,
            valor_venda_m2=estudo.valor_venda_m2,
            custo_obra_m2=estudo.custo_obra_m2,
            zona_detectada=zona
        )
        
        db.add(novo_estudo)
        db.commit()
        db.refresh(novo_estudo)
        return novo_estudo
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))