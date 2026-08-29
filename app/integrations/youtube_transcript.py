import re
from fastapi import status
from youtube_transcript_api import YouTubeTranscriptApi
from app.main import AppException

def extract_youtube_video_id(url: str) -> str:
    """Extracts YouTube video ID from standard or shortened URLs."""
    pattern = r"(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})"
    match = re.search(pattern, url)
    if not match:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_YOUTUBE_URL",
            message="Invalid YouTube video URL format."
        )
    return match.group(1)

def fetch_youtube_transcript(video_url: str) -> str:
    """Extracts audio transcript text from YouTube video."""
    video_id = extract_youtube_video_id(video_url)

    try:
        api_response = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "hi"])
        transcript_text = " ".join([item["text"] for item in api_response])
        if not transcript_text or len(transcript_text) < 20:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="TRANSCRIPT_UNAVAILABLE",
                message="YouTube video audio transcript is empty."
            )
        return transcript_text[:15000]
    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="TRANSCRIPT_UNAVAILABLE",
            message="Audio transcript is unavailable for this YouTube video. Please upload a photo or text recipe instead.",
            details=[{"error": str(exc)}]
        )
