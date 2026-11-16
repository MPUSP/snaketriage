from __future__ import annotations

import sys
from pathlib import Path


def add_src_to_path() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"
    src_path_str = str(src_path)
    if src_path_str not in sys.path:
        sys.path.insert(0, src_path_str)
    return project_root
