from fastapi import FastAPI
from app.routes import health as health_routes  # type: ignore
app = FastAPI(title='App')
try:
    from app.routes import users  # noqa: F401
except Exception:
    pass

@app.get('/')
async def root():
    return {'status':'ok'}
