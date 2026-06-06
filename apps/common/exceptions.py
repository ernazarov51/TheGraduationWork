from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def _extract_message(detail):
    """Recursively pull the first human-readable string out of DRF detail."""
    if isinstance(detail, list):
        return _extract_message(detail[0])
    if isinstance(detail, dict):
        first_key = next(iter(detail))
        inner = _extract_message(detail[first_key])
        return f"{first_key}: {inner}"
    return str(detail)


def custom_exception_handler(exc, context):
    """Wrap every DRF error into a consistent envelope:

    {
        "success": false,
        "error": {
            "code":    "<machine-readable code>",
            "message": "<human-readable message>"
        }
    }
    """
    response = exception_handler(exc, context)

    if response is None:
        return None

    code = getattr(exc, "default_code", "error")

    if isinstance(exc, ValidationError):
        # ValidationError detail can be a dict (field errors) or a list (non-field).
        message = _extract_message(exc.detail)
        code = "validation_error"
    elif hasattr(exc, "detail"):
        message = _extract_message(exc.detail)
    else:
        message = str(exc)

    response.data = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    return response
