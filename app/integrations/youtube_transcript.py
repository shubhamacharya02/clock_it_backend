import re
import httpx
from bs4 import BeautifulSoup
from fastapi import status
from youtube_transcript_api import YouTubeTranscriptApi
from app.core.exceptions import AppException

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

def fetch_youtube_video_metadata(video_url: str) -> str:
    """Fetches video title, channel name, and description via oEmbed & HTML meta tags."""
    title = ""
    author = ""
    desc = ""
    try:
        # 1. Fetch oEmbed metadata
        oembed_url = f"https://www.youtube.com/oembed?url={video_url}&format=json"
        with httpx.Client(timeout=5.0) as client:
            res = client.get(oembed_url)
            if res.status_code == 200:
                data = res.json()
                title = data.get("title", "")
                author = data.get("author_name", "")
    except Exception:
        pass

    try:
        # 2. Fetch page meta description
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        with httpx.Client(timeout=5.0, headers=headers, follow_redirects=True) as client:
            res_html = client.get(video_url)
            if res_html.status_code == 200:
                soup = BeautifulSoup(res_html.text, "html.parser")
                meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                og_title = soup.find("meta", attrs={"property": "og:title"})
                if meta_desc and meta_desc.get("content"):
                    desc = meta_desc["content"]
                if not title and og_title and og_title.get("content"):
                    title = og_title["content"]
    except Exception:
        pass

    if title:
        parts = [f"YouTube Recipe Video Title: {title}"]
        if author:
            parts.append(f"Channel / Creator: {author}")
        if desc:
            parts.append(f"Video Description & Notes:\n{desc}")
        return "\n".join(parts)

    return f"YouTube Recipe Video: {video_url}"

def fetch_youtube_transcript(video_url: str) -> str:
    """Extracts audio transcript text from YouTube video or falls back to video title and metadata."""
    try:
        video_id = extract_youtube_video_id(video_url)
        api = YouTubeTranscriptApi()

        try:
            fetched = api.fetch(video_id, languages=["en", "en-US", "hi"])
        except Exception:
            t_list = api.list(video_id)
            first_t = next(iter(t_list))
            fetched = first_t.fetch()

        text_snippets = []
        for item in fetched:
            if hasattr(item, "text"):
                text_snippets.append(item.text)
            elif isinstance(item, dict) and "text" in item:
                text_snippets.append(item["text"])

        transcript_text = " ".join(text_snippets)
        if transcript_text and len(transcript_text) >= 20:
            return transcript_text[:15000]
    except Exception as exc:
        print(f"YouTube transcript API unavailable (falling back to video metadata): {exc}")

    return fetch_youtube_video_metadata(video_url)
