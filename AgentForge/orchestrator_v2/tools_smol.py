"""Utility helpers for the smol-style agentic pipeline.
Decoupled so we can import lightly without pulling heavy deps.
"""
from __future__ import annotations
from pathlib import Path
from typing import Iterable

IGNORES = {'.venv','__pycache__','.pytest_cache','node_modules'}

def list_files(root: Path) -> list[str]:
    out: list[str] = []
    for p in root.rglob('*'):
        if any(part in IGNORES for part in p.parts):
            continue
        if p.is_file():
            out.append(str(p.relative_to(root)))
    return out

