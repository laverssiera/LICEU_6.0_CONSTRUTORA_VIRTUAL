import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "cv-backend-core"
sys.path.insert(0, str(BACKEND_ROOT))


os.environ.setdefault("APP_NAME", "LICEU 6.0 CORE-OS")
os.environ.setdefault("VERSION", "2.0.0")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_global_config.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LICEU_CURRENCY_SYMBOL", "LC$")

from app.config import Settings


def test_global_settings_expose_new_core_configuration():
    settings = Settings()

    assert settings.APP_NAME == "LICEU 6.0 CORE-OS"
    assert settings.PROJECT_NAME == "LICEU 6.0 CORE-OS"
    assert settings.VERSION == "2.0.0"
    assert settings.ENVIRONMENT == "development"
    assert settings.SSO_SECRET_KEY == settings.JWT_SECRET_KEY
    assert settings.SSO_TOKEN_TTL_MINUTES == settings.ACCESS_TOKEN_EXPIRE_MINUTES
    assert settings.LICEU_CURRENCY_SYMBOL == "LC$"
    assert settings.URL_CEFEIDA.startswith("http://")
