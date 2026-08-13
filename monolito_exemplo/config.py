import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
TIMEOUT = int(os.getenv("TIMEOUT", "10"))
