from fastapi import APIRouter

router = APIRouter()

@router.get("/runtime/planetary-consensus")
def get_planetary_consensus():
    return {"status": "ok", "consensus": "stable"}
