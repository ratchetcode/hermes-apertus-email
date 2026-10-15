#!/usr/bin/env python3
"""Export a reviewable, Git-safe snapshot of the project-local Hermes profile."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from profile_snapshot import export_profile_snapshot


if __name__ == "__main__":
    result = export_profile_snapshot(ROOT / "runtime" / "hermes", ROOT / "agent-profile")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
