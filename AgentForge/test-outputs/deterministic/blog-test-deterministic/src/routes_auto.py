from fastapi import FastAPI
from .user import router as user_router


def register_auto_routes(app: FastAPI):
    app.include_router(user_router, prefix="")
