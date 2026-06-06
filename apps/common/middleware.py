import logging
import threading
import time

from apps.common.utils import get_client_ip

logger = logging.getLogger(__name__)

_thread_locals = threading.local()


def get_current_user():
    """Return the authenticated user for the current thread.

    We store the *request* object (not the user) so that JWT auth — which
    runs at DRF view-dispatch time, after all middleware — has already
    resolved request.user by the time BaseModel.save() calls this helper.
    """
    request = getattr(_thread_locals, "current_request", None)
    if request is None:
        return None
    return getattr(request, "user", None)


class CurrentUserMiddleware:
    """Attach the current request to thread-local storage so that
    BaseModel.save() can auto-populate created_by / updated_by.

    We store the request — not request.user — because JWT authentication
    happens inside DRF view dispatch (after all middleware has run).
    Reading request.user from within a model save() call is safe because
    by that point DRF has already authenticated the token and set
    request.user on the underlying WSGIRequest object.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.current_request = request
        try:
            return self.get_response(request)
        finally:
            _thread_locals.current_request = None


class RequestLogMiddleware:
    """Log every HTTP request: user, IP, method, path, status code, duration."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        user = getattr(request, "user", None)
        user_repr = str(user.pk) if user and user.is_authenticated else "anonymous"

        logger.info(
            "method=%s path=%s status=%d user=%s ip=%s duration=%.1fms",
            request.method,
            request.path,
            response.status_code,
            user_repr,
            get_client_ip(request),
            duration_ms,
        )
        return response
