from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Lightweight health endpoint for Docker, load-balancers, and monitoring.

    Returns 200 when the app and database are reachable, 503 otherwise.
    """
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    payload = {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "unreachable",
    }
    http_status = 200 if db_ok else 503
    return Response(payload, status=http_status)
