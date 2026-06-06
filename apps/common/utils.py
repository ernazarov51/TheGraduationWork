from typing import Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response


def get_client_ip(request: Request) -> str:
    """Return the real client IP, respecting X-Forwarded-For from reverse proxies."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def make_error(
    code: str,
    message: str,
    http_status: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    """Return a standardised error response.

    Shape: {"success": false, "error": {"code": "...", "message": "..."}}
    """
    return Response(
        {"success": False, "error": {"code": code, "message": message}},
        status=http_status,
    )


def make_success(
    data: Any = None,
    http_status: int = status.HTTP_200_OK,
) -> Response:
    """Return a standardised success response.

    Shape: {"success": true, "data": ...}
    """
    return Response({"success": True, "data": data}, status=http_status)
