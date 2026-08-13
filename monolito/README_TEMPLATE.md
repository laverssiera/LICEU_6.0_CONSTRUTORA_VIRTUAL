# Estrutura base para monolito padrão LICEU 6.0

monolito/
├── main.py
├── handlers/
│   └── __init__.py
├── publishers/
│   └── __init__.py
├── config.py

# main.py
import uvicorn
from fastapi import FastAPI
from handlers import register_handlers
from publishers import register_publishers

app = FastAPI()

@app.get("/health")
def healthcheck():
    return {"status": "ok"}

# Startup padronizado
@app.on_event("startup")
def startup_event():
    register_handlers(app)
    register_publishers(app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# handlers/__init__.py

def register_handlers(app):
    # Exemplo: app.post("/process")(process_handler)
    pass

# publishers/__init__.py

def register_publishers(app):
    # Exemplo: inicialização de publishers/eventos
    pass

# config.py

import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
TIMEOUT = int(os.getenv("TIMEOUT", "10"))
