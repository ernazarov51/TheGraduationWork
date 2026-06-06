from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.courses.models import Course, Group, Lesson, Section, Topic
from apps.users.serializers import UserSerializer

User = get_user_model()


class LessonSerializer(serializers.ModelSerializer):
    has_video = serializers.SerializerMethodField()
    video_status = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = (
            "id", "title", "description", "order", "duration",
            "has_video", "video_status", "created_at",
        )
        read_only_fields = ("id", "duration", "created_at")

    def get_has_video(self, obj):
        return hasattr(obj, "video")

    def get_video_status(self, obj):
        if hasattr(obj, "video"):
            return obj.video.status
        return None


class LessonWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ("id", "topic", "title", "description", "order")
        read_only_fields = ("id",)


class TopicSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = ("id", "title", "description", "order", "lessons", "created_at")
        read_only_fields = ("id", "created_at")


class TopicWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ("id", "section", "title", "description", "order")
        read_only_fields = ("id",)


class SectionSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)

    class Meta:
        model = Section
        fields = ("id", "title", "order", "topics", "created_at")
        read_only_fields = ("id", "created_at")


class SectionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ("id", "course", "title", "order")
        read_only_fields = ("id",)


class CourseListSerializer(serializers.ModelSerializer):
    teacher = UserSerializer(read_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(
        source="teacher",
        queryset=User.objects.filter(role="teacher"),
        write_only=True,
    )
    sections_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "id", "title", "description", "teacher", "teacher_id",
            "is_published", "sections_count", "created_at",
        )
        read_only_fields = ("id", "created_at")

    def get_sections_count(self, obj):
        return obj.sections.count()


class CourseDetailSerializer(CourseListSerializer):
    sections = SectionSerializer(many=True, read_only=True)

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ("sections",)


# ── Group serializers ─────────────────────────────────────────────────────────

class GroupSerializer(serializers.ModelSerializer):
    students = UserSerializer(many=True, read_only=True)
    student_ids = serializers.PrimaryKeyRelatedField(
        source="students",
        many=True,
        queryset=User.objects.filter(role="student"),
        write_only=True,
        required=False,
    )
    courses_detail = CourseListSerializer(source="courses", many=True, read_only=True)
    course_ids = serializers.PrimaryKeyRelatedField(
        source="courses",
        many=True,
        queryset=Course.objects.filter(is_active=True),
        write_only=True,
        required=False,
    )
    students_count = serializers.SerializerMethodField()
    courses_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = (
            "id", "name",
            "students", "student_ids",
            "courses_detail", "course_ids",
            "students_count", "courses_count",
            "is_active", "created_at",
        )
        read_only_fields = ("id", "created_at")

    def get_students_count(self, obj):
        return obj.students.count()

    def get_courses_count(self, obj):
        return obj.courses.count()


class GroupMemberSerializer(serializers.Serializer):
    """Guruhga student yoki course qo'shish/chiqarish uchun."""
    id = serializers.UUIDField()
