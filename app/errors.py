from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


ERROR_MESSAGES = {
    status.HTTP_401_UNAUTHORIZED: "Unauthorized",
    status.HTTP_403_FORBIDDEN: "Forbidden",
    status.HTTP_404_NOT_FOUND: "Not found",
}


def error_response(status_code: int, message: str, detail) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": message,
            "detail": detail,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
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
        return error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Validation error",
            exc.errors(),
        )
