import subprocess
from pathlib import Path

from celery import shared_task
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_video(self, video_id):
    from apps.videos.models import Video

    try:
        video = Video.objects.select_related("lesson").get(id=video_id)
    except Video.DoesNotExist:
        return {"error": "Video not found"}

    video.status = Video.PROCESSING
    video.save(update_fields=["status", "updated_at"])

    output_dir = Path(settings.MEDIA_ROOT) / "videos" / str(video.lesson_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = video.original_file.path
    output_m3u8 = str(output_dir / "master.m3u8")
    segment_pattern = str(output_dir / "segment_%03d.ts")

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "copy",
        "-c:a", "copy",
        "-start_number", "0",
        "-hls_time", "10",
        "-hls_list_size", "0",
        "-hls_segment_filename", segment_pattern,
        "-f", "hls",
        output_m3u8,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            video.status = Video.FAILED
            video.error_message = result.stderr[:2000]
            video.save(update_fields=["status", "error_message", "updated_at"])
            return {"error": video.error_message}

        # Get video duration via ffprobe
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path,
        ]
        probe = subprocess.run(probe_cmd, capture_output=True, text=True)
        duration = 0
        if probe.returncode == 0:
            try:
                duration = int(float(probe.stdout.strip()))
            except (ValueError, TypeError):
                pass

        video.status = Video.READY
        video.hls_path = f"videos/{video.lesson_id}/master.m3u8"
        video.duration = duration
        video.save(update_fields=["status", "hls_path", "duration", "updated_at"])

        # Sync duration to Lesson
        video.lesson.duration = duration
        video.lesson.save(update_fields=["duration", "updated_at"])

        return {"status": "ready", "duration": duration}

    except subprocess.TimeoutExpired:
        video.status = Video.FAILED
        video.error_message = "FFmpeg processing timed out (>10 min)"
        video.save(update_fields=["status", "error_message", "updated_at"])
        return {"error": video.error_message}

    except Exception as exc:
        video.status = Video.FAILED
        video.error_message = str(exc)[:500]
        video.save(update_fields=["status", "error_message", "updated_at"])
        raise self.retry(exc=exc)
