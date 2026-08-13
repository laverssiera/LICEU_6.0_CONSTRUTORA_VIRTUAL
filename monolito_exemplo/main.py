
import uvicorn
from fastapi import FastAPI, Request
from handlers import register_handlers
from publishers import register_publishers
from monolito.logging_config import setup_logging, get_correlation_id, set_correlation_id


setup_logging()
app = FastAPI()


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    cid = request.headers.get("x-correlation-id")
    if not cid:
        cid = get_correlation_id()
    set_correlation_id(cid)
    response = await call_next(request)
    response.headers["x-correlation-id"] = cid
    return response

@app.get("/health")
def healthcheck():
    import logging
    logger = logging.getLogger("healthcheck")
    logger.info("Healthcheck OK", extra={"correlation_id": get_correlation_id()})
    return {"status": "ok", "correlation_id": get_correlation_id()}

@app.on_event("startup")
def startup_event():
    register_handlers(app)
    register_publishers(app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
