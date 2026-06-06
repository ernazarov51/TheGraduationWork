from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Course(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="courses",
        limit_choices_to={"role": "teacher"},
    )
    is_published = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Section(BaseModel):
    """Bo'lim — bir kurs ichidagi bo'lim."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} / {self.title}"


class Topic(BaseModel):
    """Mavzu — bo'lim ichidagi mavzu."""

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Topic"
        verbose_name_plural = "Topics"
        ordering = ["order"]

    def __str__(self):
        return f"{self.section.title} / {self.title}"


class Lesson(BaseModel):
    """Video dars — mavzu ichidagi dars."""

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    duration = models.PositiveIntegerField(default=0, help_text="Duration in seconds")

    class Meta:
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        ordering = ["order"]

    def __str__(self):
        return self.title


class Group(BaseModel):
    """
    Talabalar guruhi.
    Bir guruhga bir nechta student va bir nechta course biriktiriladi (M2M).
    """

    name = models.CharField(max_length=255)
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="student_groups",
        blank=True,
        limit_choices_to={"role": "student"},
    )
    courses = models.ManyToManyField(
        Course,
        related_name="groups",
        blank=True,
    )

    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
