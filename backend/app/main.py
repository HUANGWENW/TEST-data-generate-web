from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import projects, tasks
from app.core.config import get_settings
from app.core.database import Base, engine
from app.models import entities  # noqa: F401
from app.services.storage import storage_root


settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    storage_root()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get(f"{settings.api_prefix}/health")
def api_health():
    return {"status": "ok"}


app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(tasks.router, prefix=settings.api_prefix)
app.mount("/storage", StaticFiles(directory=str(storage_root())), name="storage")
