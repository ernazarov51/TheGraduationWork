from django.contrib import admin

from apps.courses.models import Course, Group, Lesson, Section, Topic


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0
    fields = ("title", "order", "is_active")


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 0
    fields = ("title", "order", "is_active")


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ("title", "order", "duration", "is_active")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "teacher", "is_published", "is_active", "created_at")
    list_filter = ("is_published", "is_active")
    search_fields = ("title", "teacher__phone", "teacher__full_name")
    inlines = [SectionInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "course__title")
    inlines = [TopicInline]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title",)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "topic", "order", "duration", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title",)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "get_students_count", "get_courses_count", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    filter_horizontal = ("students", "courses")

    @admin.display(description="Students")
    def get_students_count(self, obj):
        return obj.students.count()

    @admin.display(description="Courses")
    def get_courses_count(self, obj):
        return obj.courses.count()
