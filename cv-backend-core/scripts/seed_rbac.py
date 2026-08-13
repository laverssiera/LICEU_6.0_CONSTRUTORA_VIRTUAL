from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import SessionLocal
from app.services.rbac_seed import seed_rbac_defaults


def main() -> None:
    db = SessionLocal()
    try:
        summary = seed_rbac_defaults(db)
        print({"status": "ok", **summary})
    finally:
        db.close()


if __name__ == "__main__":
    main()
