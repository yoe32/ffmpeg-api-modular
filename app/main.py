from fastapi import FastAPI
from app.core.config import settings
from app.api.routers.health import router as health_router
from app.api.routers.probe import router as probe_router
from app.api.routers.process import router as process_router
docs_url = "/docs" if settings.DOCS_ENABLED else None
redoc_url = "/redoc" if settings.DOCS_ENABLED else None
openapi_url = "/openapi.json" if settings.DOCS_ENABLED else None
app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION, description=settings.API_DESCRIPTION, docs_url=docs_url, redoc_url=redoc_url, openapi_url=openapi_url)
app.include_router(health_router); app.include_router(probe_router); app.include_router(process_router)
