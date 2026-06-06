from rest_framework import serializers

from apps.videos.models import Video


class VideoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ("id", "lesson", "original_file")
        read_only_fields = ("id",)

    def validate_lesson(self, lesson):
        if hasattr(lesson, "video"):
            raise serializers.ValidationError("This lesson already has a video.")
        return lesson


class VideoStatusSerializer(serializers.ModelSerializer):
    stream_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            "id", "lesson", "status", "duration",
            "stream_url", "error_message", "created_at", "updated_at",
        )
        read_only_fields = fields

    def get_stream_url(self, obj):
        if obj.status != Video.READY or not obj.hls_path:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/media/{obj.hls_path}")
        return f"/media/{obj.hls_path}"
