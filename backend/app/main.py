"""Application entry point: wiring, CORS and error mapping."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import meta, trips
from app.core.config import get_settings
from app.db import init_db
from app.services.trip_service import ConflictError, DomainValidationError, NotFoundError


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
        expose_headers=["Location"],
    )

    # Domain exceptions -> HTTP status codes (keeps services framework-agnostic).
    def _handler(code: int):
        async def handle(_: Request, exc: Exception):
            return JSONResponse(status_code=code, content={"detail": str(exc)})

        return handle

    app.add_exception_handler(NotFoundError, _handler(404))
    app.add_exception_handler(ConflictError, _handler(409))
    app.add_exception_handler(DomainValidationError, _handler(422))

    app.include_router(trips.router)
    app.include_router(meta.router)
    return app


app = create_app()
