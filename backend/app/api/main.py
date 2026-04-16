"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from ..config import get_settings, print_config, validate_config
from ..db.database import init_db
from .routes import auth, collab, community, feedback, kb, map as map_routes, poi, tracks, trip, user

settings = get_settings()


class _UvicornAccessNoiseFilter(logging.Filter):
    """Drop very noisy local health/root probes from uvicorn access logs."""

    _ignored_fragments = (
        '"GET / HTTP/',
        '"GET /health HTTP/',
    )

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(fragment in message for fragment in self._ignored_fragments)


def _install_access_log_filter() -> None:
    access_logger = logging.getLogger("uvicorn.access")
    if any(isinstance(item, _UvicornAccessNoiseFilter) for item in access_logger.filters):
        return
    access_logger.addFilter(_UvicornAccessNoiseFilter())

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Travel planning API with multi-agent orchestration, profile, memory, and local knowledge base.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(poi.router, prefix="/api")
app.include_router(map_routes.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(kb.router, prefix="/api")
app.include_router(tracks.router, prefix="/api")
app.include_router(community.router, prefix="/api")
app.include_router(collab.router, prefix="/api")
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.middleware("http")
async def force_utf8_json_charset(request: Request, call_next) -> Response:
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("application/json") and "charset=" not in content_type.lower():
        response.headers["content-type"] = f"{content_type}; charset=utf-8"
    return response


@app.middleware("http")
async def log_api_json_response(request: Request, call_next) -> Response:
    response = await call_next(request)

    if not request.url.path.startswith("/api"):
        return response

    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type.lower():
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    text = body.decode("utf-8", errors="replace")
    if len(text) > 4000:
        text = text[:4000] + "...<truncated>"

    print(
        f"[API] {request.method} {request.url.path} -> {response.status_code} body={text}",
        flush=True,
    )

    return Response(
        content=body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=response.background,
    )


@app.on_event("startup")
async def startup_event() -> None:
    print("\n" + "=" * 60)
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print("=" * 60)

    _install_access_log_filter()
    print_config()
    validate_config()
    init_db()

    print("\nAPI docs: http://localhost:8000/docs")
    print("ReDoc: http://localhost:8000/redoc")
    print("=" * 60 + "\n")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    print("\n" + "=" * 60)
    print("Shutting down application...")
    print("=" * 60 + "\n")


@app.get("/")
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
