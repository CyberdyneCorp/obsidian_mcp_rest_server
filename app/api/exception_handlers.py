"""Centralized exception handlers for FastAPI."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import DomainException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""

    @app.exception_handler(DomainException)
    async def domain_exception_handler(
        request: Request, exc: DomainException
    ) -> JSONResponse:
        """Handle all domain exceptions uniformly.

        Converts DomainException subclasses to appropriate HTTP responses
        using their http_status and to_dict() methods.
        """
        logger.warning(
            f"Domain exception: {exc.code} - {exc.message}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "exception_code": exc.code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_dict(),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions.

        Logs the full error and returns a generic 500 response.
        """
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
            exc_info=True,
        )

        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            },
        )
