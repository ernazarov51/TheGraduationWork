from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView

from apps.common.views import health_check

schema_view = get_schema_view(
    openapi.Info(
        title="EduStream API",
        default_version="v1",
        description="Masofaviy ta'lim platformasi — video oqimli dars tizimi",
        contact=openapi.Contact(email="admin@example.com"),
        license=openapi.License(name="MIT"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Health check
    path("api/health/", health_check, name="health-check"),

    # Auth
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Courses, Sections, Topics, Lessons, Enrollments
    path("api/v1/", include("apps.courses.urls")),

    # Video upload & streaming
    path("api/v1/videos/", include("apps.videos.urls")),

    # Swagger / ReDoc
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
