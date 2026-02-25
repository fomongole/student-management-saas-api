import logging
import re
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError


logger = logging.getLogger("app.exceptions")
logging.basicConfig(level=logging.INFO)

# BASE DOMAIN EXCEPTION
class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
        
        
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
        
    logger.error(
        f"Unhandled server error: {exc}",
        exc_info=True,
        extra={"path": request.url.path}
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred on the server.",
            }
        }
    )

# GENERIC DOMAIN ERRORS
class ForbiddenException(AppException):
    def __init__(self, message: str = "You are not allowed to perform this action."):
        super().__init__("FORBIDDEN", message, 403)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found."):
        super().__init__("NOT_FOUND", message, 404)


class ConflictException(AppException):
    def __init__(self, code: str, message: str):
        super().__init__(code, message, 400)


class ValidationFailedException(AppException):
    def __init__(self, fields: dict):
        self.fields = fields
        super().__init__("VALIDATION_ERROR", "Validation failed.", 422)


# SPECIFIC DOMAIN ERRORS
class SchoolAlreadyExistsException(ConflictException):
    def __init__(self):
        super().__init__(
            "SCHOOL_ALREADY_EXISTS",
            "A school with this email is already registered.",
        )


class UserEmailAlreadyExistsException(ConflictException):
    def __init__(self):
        super().__init__(
            "EMAIL_ALREADY_REGISTERED",
            "Email already registered.",
        )


class ClassAlreadyExistsException(ConflictException):
    def __init__(self):
        super().__init__(
            "CLASS_ALREADY_EXISTS",
            "A class with this name and stream already exists.",
        )


class SubjectAlreadyExistsException(ConflictException):
    def __init__(self):
        super().__init__(
            "SUBJECT_ALREADY_EXISTS",
            "Subject code already exists.",
        )

# HANDLERS
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(
        "Application exception",
        extra={"path": request.url.path, "code": exc.code},
    )

    response = {
        "error": {
            "code": exc.code,
            "message": exc.message,
        }
    }

    if isinstance(exc, ValidationFailedException):
        response["error"]["fields"] = exc.fields

    return JSONResponse(status_code=exc.status_code, content=response)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    fields = {e["loc"][-1]: e["msg"] for e in exc.errors()}
    return await app_exception_handler(request, ValidationFailedException(fields))

# INTEGRITY FALLBACK
CONSTRAINT_CODE_MAP = {
    "_school_class_stream_uc": "CLASS_ALREADY_EXISTS",
}

CONSTRAINT_MESSAGE_MAP = {
    "_school_class_stream_uc": "A class with this name and stream already exists.",
}


def extract_constraint_name(exc: IntegrityError) -> str | None:
    if hasattr(exc.orig, "diag") and exc.orig.diag.constraint_name:
        return exc.orig.diag.constraint_name
    match = re.search(r'constraint "(.*?)"', str(exc.orig))
    return match.group(1) if match else None


async def integrity_error_handler(request: Request, exc: IntegrityError):
    constraint = extract_constraint_name(exc)
    code = CONSTRAINT_CODE_MAP.get(constraint, "INTEGRITY_ERROR")
    message = CONSTRAINT_MESSAGE_MAP.get(
        constraint,
        "Database integrity violation.",
    )
    return JSONResponse(
        status_code=400,
        content={"error": {"code": code, "message": message}},
    )