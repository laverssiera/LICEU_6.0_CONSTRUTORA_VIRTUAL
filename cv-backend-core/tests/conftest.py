import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("APP_NAME", "LICEU 6.0 CORE-OS")
os.environ.setdefault("VERSION", "2.0.0")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_cv_backend_core.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
