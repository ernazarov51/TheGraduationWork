from django.db import models

from apps.common.models import BaseModel


class Video(BaseModel):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (PROCESSING, "Processing"),
        (READY, "Ready"),
        (FAILED, "Failed"),
    ]

    lesson = models.OneToOneField(
        "courses.Lesson",
        on_delete=models.CASCADE,
        related_name="video",
    )
    original_file = models.FileField(upload_to="videos/originals/")
    hls_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    duration = models.PositiveIntegerField(default=0, help_text="Duration in seconds")
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Video for lesson: {self.lesson.title} [{self.status}]"

    @property
    def hls_url(self):
        if self.hls_path and self.status == self.READY:
            return self.hls_path
        return None
