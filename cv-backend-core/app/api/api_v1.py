from fastapi import APIRouter
from .endpoints import schedule, project_consistency

api_router = APIRouter()
api_router.include_router(schedule.router, prefix="", tags=["schedule"])
api_router.include_router(project_consistency.router, prefix="/projects", tags=["project-consistency"])
