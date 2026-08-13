from fastapi import APIRouter

router = APIRouter()

@router.get("/federation/events/{event_id}/lineage")
def get_event_lineage(event_id: str):
    """
    Rastreia a teia temporal completa. 
    Ex: MISSION_CREATED -> ANCHORS_APPROVED -> JOHN_PLANNED -> OPERA_EXECUTED -> ARCHIMEDES_UPDATED
    """
    
    # Exemplo mock com a exata arquitetura temporal de dependência do LICEU.
    dummy_lineage = [
        "MISSION_CREATED",
        "ANCHORS_APPROVED",
        "JOHN_PLANNED",
        "OPERA_EXECUTED",
        "ARCHIMEDES_UPDATED"
    ]
    
    return {
        "event_id": event_id,
        "lineage": dummy_lineage
    }