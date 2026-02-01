"""
Centralized exception handling system for Django REST Framework.

This module provides a custom exception handler that standardizes error responses
across the entire project, including proper error codes, messages, and logging.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import IntegrityError

from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

# Optional imports for SimpleJWT
try:
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
except ImportError:
    InvalidToken = None
    TokenError = None

# Logger
logger = logging.getLogger(__name__)


class BusinessException(Exception):
    """
    Base class for custom business exceptions.

    Subclasses should define error_code, error_message, and status_code.
    """

    error_code: str = "BUSINESS_ERROR"
    error_message: str = "Business logic error"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(
        self, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message or self.error_message)
        self.details = details or {}


# Example custom exceptions (uncomment and customize as needed)
# class WorkspaceAccessDenied(BusinessException):
#     error_code = "WORKSPACE_ACCESS_DENIED"
#     error_message = "Access denied to workspace"
#     status_code = status.HTTP_403_FORBIDDEN
#
# class CrossWorkspaceOperationError(BusinessException):
#     error_code = "CROSS_WORKSPACE_OPERATION"
#     error_message = "Operation not allowed across workspaces"
#     status_code = status.HTTP_400_BAD_REQUEST
#
# class AssignmentValidationError(BusinessException):
#     error_code = "ASSIGNMENT_VALIDATION_ERROR"
#     error_message = "Assignment validation failed"
#     status_code = status.HTTP_400_BAD_REQUEST


# Error code mappings
ERROR_MAPPINGS: Dict[type, Tuple[str, str, int]] = {
    ValidationError: (
        "VALIDATION_ERROR",
        "Validation failed",
        status.HTTP_400_BAD_REQUEST,
    ),
    NotAuthenticated: (
        "AUTH_REQUIRED",
        "Authentication required",
        status.HTTP_401_UNAUTHORIZED,
    ),
    AuthenticationFailed: (
        "AUTH_FAILED",
        "Authentication failed",
        status.HTTP_401_UNAUTHORIZED,
    ),
    PermissionDenied: (
        "PERMISSION_DENIED",
        "Permission denied",
        status.HTTP_403_FORBIDDEN,
    ),
    NotFound: ("RESOURCE_NOT_FOUND", "Resource not found", status.HTTP_404_NOT_FOUND),
    MethodNotAllowed: (
        "METHOD_NOT_ALLOWED",
        "Method not allowed",
        status.HTTP_405_METHOD_NOT_ALLOWED,
    ),
    ParseError: ("PARSE_ERROR", "Parse error", status.HTTP_400_BAD_REQUEST),
    Throttled: ("THROTTLED", "Request throttled", status.HTTP_429_TOO_MANY_REQUESTS),
    ObjectDoesNotExist: (
        "RESOURCE_NOT_FOUND",
        "Resource not found",
        status.HTTP_404_NOT_FOUND,
    ),
    IntegrityError: (
        "DATABASE_CONSTRAINT_ERROR",
        "Database constraint violation",
        status.HTTP_400_BAD_REQUEST,
    ),
    MultipleObjectsReturned: (
        "MULTIPLE_OBJECTS_RETURNED",
        "Multiple objects returned",
        status.HTTP_400_BAD_REQUEST,
    ),
}

# Add SimpleJWT errors if available
if TokenError:
    ERROR_MAPPINGS[TokenError] = (
        "TOKEN_INVALID",
        "Invalid token",
        status.HTTP_401_UNAUTHORIZED,
    )
if InvalidToken:
    ERROR_MAPPINGS[InvalidToken] = (
        "TOKEN_INVALID",
        "Invalid token",
        status.HTTP_401_UNAUTHORIZED,
    )


def get_error_details(exc: Exception) -> Tuple[str, str, int, Dict[str, Any]]:
    """
    Get standardized error details for an exception.

    Args:
        exc: The exception instance.

    Returns:
        Tuple of (error_code, error_message, status_code, details)
    """
    # Handle custom business exceptions
    if isinstance(exc, BusinessException):
        return (exc.error_code, exc.error_message, exc.status_code, exc.details)

    for exc_class, (code, message, status_code) in ERROR_MAPPINGS.items():
        if isinstance(exc, exc_class):
            details = getattr(exc, "detail", {}) if hasattr(exc, "detail") else {}
            return code, message, status_code, details

    # Default for unknown exceptions
    return (
        "INTERNAL_SERVER_ERROR",
        "An unexpected error occurred",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        {},
    )


def custom_exception_handler(
    exc: Exception, context: Dict[str, Any]
) -> Optional[Response]:
    """
    Custom exception handler that provides standardized error responses.

    This handler extends Django REST Framework's default exception handler
    and ensures all errors follow a consistent response format.

    Args:
        exc: The exception instance.
        context: The context dictionary containing request and other info.

    Returns:
        A Response object with standardized error format, or None if unhandled.
    """
    # Get error details
    error_code, error_message, status_code, details = get_error_details(exc)

    # For DRF exceptions, try to use the default handler first
    response = exception_handler(exc, context)
    if response:
        # Override with standardized format
        response.data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": error_message,
                "details": response.data,
            },
            "status_code": response.status_code,
        }
        response.status_code = status_code
    else:
        # For non-DRF exceptions or unhandled cases
        response = Response(
            {
                "success": False,
                "error": {
                    "code": error_code,
                    "message": error_message,
                    "details": details,
                },
                "status_code": status_code,
            },
            status=status_code,
        )

    # Logging
    request = context.get("request")
    user_id = (
        request.user.id
        if request and hasattr(request, "user") and request.user.is_authenticated
        else "Anonymous"
    )
    path = request.path if request else "Unknown"

    logger.error(
        f"Exception: {type(exc).__name__}, "
        f"Message: {str(exc)}, "
        f"Path: {path}, "
        f"User: {user_id}, "
        f"Error Code: {error_code}"
    )

    return response
