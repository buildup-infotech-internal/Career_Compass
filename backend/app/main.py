import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import Settings, settings
from app.core.responses import success_response
from app.db.session import dispose_database

logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Release any lazily-created database connections on application shutdown."""
    yield
    dispose_database()


def create_app(app_settings: Settings = settings) -> FastAPI:
    application = FastAPI(
        title=app_settings.APP_NAME,
        description="AI-powered career guidance and job search platform.",
        version="1.0.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )
    application.include_router(api_router, prefix=app_settings.API_V1_PREFIX)

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        errors = exc.detail if isinstance(exc.detail, list) else []
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": message, "errors": errors},
            headers=exc.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = [
            {
                "loc": list(error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Request validation failed",
                "errors": errors,
            },
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An unexpected error occurred",
                "errors": [],
            },
        )

    @application.get("/", tags=["Health"])
    def root() -> dict[str, object]:
        return success_response("Welcome to the Career Compass API!")

    @application.get("/health", tags=["Health"])
    def health_check() -> dict[str, object]:
        return success_response("API is healthy and running")

    return application


app = create_app()