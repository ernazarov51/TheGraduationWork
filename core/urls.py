from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView

from apps.common.views import health_check

schema_view = get_schema_view(
    openapi.Info(
        title="DRF Template API",
        default_version="v1",
        description="Universal DRF template — phone-based auth with JWT",
        contact=openapi.Contact(email="admin@example.com"),
        license=openapi.License(name="MIT"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Health check — no auth required (Docker, monitoring, load-balancers)
    path("api/health/", health_check, name="health-check"),

    # API v1
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Swagger / ReDoc
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
]
