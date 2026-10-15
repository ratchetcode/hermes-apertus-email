#!/usr/bin/env python3
"""Apply the versioned, Git-safe Hermes profile to the local runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from profile_snapshot import apply_profile_to_runtime


if __name__ == "__main__":
    result = apply_profile_to_runtime(ROOT / "agent-profile", ROOT / "runtime" / "hermes")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
