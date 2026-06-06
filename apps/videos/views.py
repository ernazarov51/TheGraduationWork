from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsTeacherOrDirector
from apps.courses.models import Lesson
from apps.videos.models import Video
from apps.videos.serializers import VideoStatusSerializer, VideoUploadSerializer
from apps.videos.tasks import process_video


class VideoUploadView(generics.CreateAPIView):
    """
    POST /api/v1/videos/upload/
    Body: lesson (UUID), original_file (file)
    Triggers async FFmpeg → HLS processing via Celery.
    """

    serializer_class = VideoUploadSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrDirector]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video = serializer.save()
        process_video.delay(str(video.id))
        status_serializer = VideoStatusSerializer(video, context={"request": request})
        return Response(
            {"success": True, "data": status_serializer.data},
            status=status.HTTP_201_CREATED,
        )


class VideoStreamView(APIView):
    """
    GET /api/v1/videos/<lesson_id>/stream/
    Returns the HLS master playlist URL for HLS.js player.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id, is_active=True)
        except Lesson.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "not_found", "message": "Lesson not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not hasattr(lesson, "video"):
            return Response(
                {"success": False, "error": {"code": "no_video", "message": "No video uploaded for this lesson."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        video = lesson.video
        if video.status != Video.READY:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "not_ready",
                        "message": f"Video is not ready yet. Status: {video.status}",
                    },
                },
                status=status.HTTP_202_ACCEPTED,
            )

        stream_url = request.build_absolute_uri(f"/media/{video.hls_path}")
        return Response(
            {
                "success": True,
                "data": {
                    "lesson_id": str(lesson_id),
                    "stream_url": stream_url,
                    "duration": video.duration,
                },
            }
        )


class VideoStatusView(generics.RetrieveAPIView):
    """
    GET /api/v1/videos/<video_id>/status/
    Returns the current processing status of the video.
    """

    serializer_class = VideoStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "video_id"

    def get_queryset(self):
        return Video.objects.select_related("lesson").filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={"request": request})
        return Response({"success": True, "data": serializer.data})
