"""
File operation models for agentic code generation.
Uses Pydantic v1 for compatibility with smolagents.
"""
from pydantic import BaseModel
from typing import List, Literal

class FileOp(BaseModel):
    """Single file operation"""
    path: str                           # ex: "src/models.py", "src/routes/users.py"
    action: Literal["write"] = "write"  # MVP: only "write" allowed
    language: str                       # "python","md","yaml","toml"
    content: str

class FileOps(BaseModel):
    """Collection of file operations"""
    operations: List[FileOp] = []