import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://liceu:liceu@postgres:5432/liceu")
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
