from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routers.auth import router as auth_router
from api.routers.projects import router as projects_router
from database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="EscrowFlow API",
    version="1.0.0",
    description="Structured FastAPI endpoints for authentication and project CRUD.",
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "EscrowFlow API is running."}


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
