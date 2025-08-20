# Pydantic v1
from pydantic import BaseModel
from typing import List, Literal

class FileOp(BaseModel):
    path: str                           # ex: "src/models.py", "src/routes/users.py"
    action: Literal["write"] = "write"  # MVP: on n'autorise que "write"
    language: str                       # "python","md","yaml","toml"
    content: str

class FileOps(BaseModel):
    operations: List[FileOp] = []