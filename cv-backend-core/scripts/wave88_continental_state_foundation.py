from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.continental.wave88_continental_state_foundation import ContinentalStateFoundation


def run(w87_envelope: dict) -> dict:
    return ContinentalStateFoundation().execute(w87_envelope)


def main() -> None:
    envelope = json.load(sys.stdin)
    print(json.dumps(run(envelope), ensure_ascii=True))


if __name__ == "__main__":
    main()