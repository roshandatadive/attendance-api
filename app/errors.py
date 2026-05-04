from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import json


ERROR_MESSAGES = {
    status.HTTP_401_UNAUTHORIZED: "Unauthorized",
    status.HTTP_403_FORBIDDEN: "Forbidden",
    status.HTTP_404_NOT_FOUND: "Not found",
}


def _serialize_value(value):
    """
    Recursively convert bytes and other non-JSON-serializable types to strings.
    Fixes: TypeError when validation errors contain bytes (e.g., from request body).
    """
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def error_response(status_code: int, message: str, detail) -> JSONResponse:
    """
    Create consistent error response with safe JSON serialization.
    Structure: {"message": "...", "detail": ...}
    """
    # Safely serialize detail to avoid bytes serialization errors
    serialized_detail = _serialize_value(detail)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "message": message,
            "detail": serialized_detail,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        # Handle known HTTP errors with predefined messages
        if exc.status_code in ERROR_MESSAGES:
            response = error_response(
                exc.status_code,
                ERROR_MESSAGES[exc.status_code],
                exc.detail,
            )
            response.headers.update(exc.headers or {})
            return response

        return error_response(exc.status_code, "Error", exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors safely.
        Converts exc.errors() (which may contain bytes) to safe JSON format.
        """
        return error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Validation error",
            exc.errors(),  # _serialize_value() handles bytes conversion
        )
