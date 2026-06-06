from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsTeacherOrDirector
from apps.courses.models import Course, Group, Lesson, Section, Topic
from apps.courses.serializers import (
    CourseDetailSerializer,
    CourseListSerializer,
    GroupMemberSerializer,
    GroupSerializer,
    LessonSerializer,
    LessonWriteSerializer,
    SectionSerializer,
    SectionWriteSerializer,
    TopicSerializer,
    TopicWriteSerializer,
)

User = get_user_model()


class CourseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_published", "teacher"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "title"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseListSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsTeacherOrDirector()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Course.objects.select_related("teacher").prefetch_related("sections").filter(is_active=True)
        if user.role == "student":
            # Student faqat o'z guruhidagi kurslarni ko'radi
            return qs.filter(groups__students=user, groups__is_active=True).distinct()
        if user.role == "teacher":
            return qs.filter(teacher=user)
        return qs  # director barchasini ko'radi

    @action(detail=False, methods=["get"], url_path="my-courses")
    def my_courses(self, request):
        user = request.user
        if user.role == "teacher":
            qs = Course.objects.filter(teacher=user, is_active=True)
        elif user.role == "student":
            qs = Course.objects.filter(
                groups__students=user, groups__is_active=True, is_active=True
            ).distinct()
        else:
            qs = Course.objects.filter(is_active=True)
        serializer = CourseListSerializer(qs, many=True, context={"request": request})
        return Response({"success": True, "data": serializer.data})


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.select_related("course").prefetch_related("topics").filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["course"]

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return SectionWriteSerializer
        return SectionSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsTeacherOrDirector()]
        return [permissions.IsAuthenticated()]


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.select_related("section__course").prefetch_related("lessons").filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["section"]

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return TopicWriteSerializer
        return TopicSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsTeacherOrDirector()]
        return [permissions.IsAuthenticated()]


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.select_related("topic__section__course").filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["topic"]

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return LessonWriteSerializer
        return LessonSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), IsTeacherOrDirector()]
        return [permissions.IsAuthenticated()]


class GroupViewSet(viewsets.ModelViewSet):
    """
    Guruh CRUD + studentlar va kurslarni qo'shish/chiqarish.

    POST /groups/{id}/add-student/    body: {"id": "<student_uuid>"}
    POST /groups/{id}/remove-student/ body: {"id": "<student_uuid>"}
    POST /groups/{id}/add-course/     body: {"id": "<course_uuid>"}
    POST /groups/{id}/remove-course/  body: {"id": "<course_uuid>"}
    """

    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrDirector]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        return Group.objects.prefetch_related("students", "courses").filter(is_active=True)

    @action(detail=True, methods=["post"], url_path="add-student")
    def add_student(self, request, pk=None):
        group = self.get_object()
        s = GroupMemberSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        student = get_object_or_404(User, id=s.validated_data["id"], role="student", is_active=True)
        group.students.add(student)
        return Response({"success": True, "detail": f"{student.full_name or student.phone} guruhga qo'shildi."})

    @action(detail=True, methods=["post"], url_path="remove-student")
    def remove_student(self, request, pk=None):
        group = self.get_object()
        s = GroupMemberSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        student = get_object_or_404(User, id=s.validated_data["id"])
        group.students.remove(student)
        return Response({"success": True, "detail": f"Student guruhdan chiqarildi."})

    @action(detail=True, methods=["post"], url_path="add-course")
    def add_course(self, request, pk=None):
        group = self.get_object()
        s = GroupMemberSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        course = get_object_or_404(Course, id=s.validated_data["id"], is_active=True)
        group.courses.add(course)
        return Response({"success": True, "detail": f'"{course.title}" kursi guruhga biriktirildi.'})

    @action(detail=True, methods=["post"], url_path="remove-course")
    def remove_course(self, request, pk=None):
        group = self.get_object()
        s = GroupMemberSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        course = get_object_or_404(Course, id=s.validated_data["id"])
        group.courses.remove(course)
        return Response({"success": True, "detail": "Kurs guruhdan chiqarildi."})
