from django.urls import path

from apps.videos.views import VideoStatusView, VideoStreamView, VideoUploadView

urlpatterns = [
    path("upload/", VideoUploadView.as_view(), name="video-upload"),
    path("<uuid:lesson_id>/stream/", VideoStreamView.as_view(), name="video-stream"),
    path("<uuid:video_id>/status/", VideoStatusView.as_view(), name="video-status"),
]
