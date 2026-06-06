from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.courses.views import (
    CourseViewSet,
    GroupViewSet,
    LessonViewSet,
    SectionViewSet,
    TopicViewSet,
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"sections", SectionViewSet, basename="section")
router.register(r"topics", TopicViewSet, basename="topic")
router.register(r"lessons", LessonViewSet, basename="lesson")
router.register(r"groups", GroupViewSet, basename="group")

urlpatterns = [
    path("", include(router.urls)),
]
