from django.contrib import admin

from apps.videos.models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("lesson", "status", "duration", "is_active", "created_at")
    list_filter = ("status", "is_active")
    search_fields = ("lesson__title",)
    readonly_fields = ("hls_path", "duration", "error_message", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("lesson", "original_file")}),
        ("Processing", {"fields": ("status", "hls_path", "duration", "error_message")}),
        ("Meta", {"fields": ("is_active", "created_at", "updated_at")}),
    )
