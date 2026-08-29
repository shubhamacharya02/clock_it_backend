import httpx
from bs4 import BeautifulSoup
from fastapi import status
from app.main import AppException

async def fetch_webpage_content(url: str) -> str:
    """Fetches HTML from target URL, strips scripts/styles/nav, and returns clean body text."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise AppException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code="URL_FETCH_FAILED",
                    message=f"Failed to fetch content from URL. Website returned HTTP {response.status_code}."
                )
            html_content = response.text
    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="URL_FETCH_FAILED",
            message="Target website URL is unreachable or timed out.",
            details=[{"error": str(exc)}]
        )

    try:
        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "header", "footer", "nav", "noscript", "aside"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        if not text or len(text) < 50:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="URL_FETCH_FAILED",
                message="Extracted webpage text content is empty or insufficient."
            )
        return text[:15000]  # Cap at 15k chars
    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="URL_FETCH_FAILED",
            message="Failed to parse webpage HTML content.",
            details=[{"error": str(exc)}]
        )
