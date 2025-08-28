from fastapi import FastAPI
from .routes import health, auth, vehicles, crud
from .db import create_tables

app = FastAPI(title="blog-test-deterministic", version="1.0.0")

# Créer les tables au démarrage
create_tables()

# Inclure les routers
app.include_router(health.router, prefix="")
app.include_router(auth.router)
app.include_router(vehicles.router)

app.include_router(crud.router)
