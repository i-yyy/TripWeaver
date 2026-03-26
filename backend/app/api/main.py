"""FastAPI 应用入口。"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from ..config import get_settings, print_config, validate_config
from ..db.database import init_db
from .routes import feedback, kb, map as map_routes, poi, trip, user

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于多智能体、用户画像、记忆与本地知识库的旅行规划 API。",
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
app.include_router(poi.router, prefix="/api")
app.include_router(map_routes.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(kb.router, prefix="/api")


@app.middleware("http")
async def force_utf8_json_charset(request: Request, call_next) -> Response:
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("application/json") and "charset=" not in content_type.lower():
        response.headers["content-type"] = f"{content_type}; charset=utf-8"
    return response


@app.on_event("startup")
async def startup_event() -> None:
    print("\n" + "=" * 60)
    print(f"启动 {settings.app_name} v{settings.app_version}")
    print("=" * 60)

    print_config()
    validate_config()
    init_db()

    print("\nAPI 文档: http://localhost:8000/docs")
    print("ReDoc 文档: http://localhost:8000/redoc")
    print("=" * 60 + "\n")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    print("\n" + "=" * 60)
    print("应用正在关闭...")
    print("=" * 60 + "\n")


@app.get("/")
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "运行中",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health() -> dict:
    return {
        "status": "健康",
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
