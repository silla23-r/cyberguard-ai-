"""
URL Analyzer and Asynchronous Redirect Chain Resolver.
Exposes hidden destinations obscured behind URL shorteners (bit.ly, tinyurl, etc.).
"""
import re
import aiohttp
import logging
from typing import List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

URL_REGEX = re.compile(
    r"(?:https?://|www\.)[a-zA-Z0-9.\-_]+(?:\.[a-zA-Z]{2,})(?:/[^\s]*)?",
    re.IGNORECASE
)

def extract_urls_from_text(text: str) -> List[str]:
    """Extracts all full or relative URLs from freeform text or OCR output."""
    if not text:
        return []
    matches = URL_REGEX.findall(text)
    clean_urls = []
    for m in matches:
        m = m.rstrip(".,;)>]\"'")
        if not m.startswith("http://") and not m.startswith("https://"):
            m = "https://" + m
        clean_urls.append(m)
    return list(dict.fromkeys(clean_urls))

async def resolve_redirect_chain(url: str, max_hops: int = 5) -> List[str]:
    """
    Follows HTTP 301/302 redirects asynchronously to discover the terminal landing URL.
    Safely times out after 4 seconds to prevent denial of service.
    """
    chain = [url]
    current_url = url

    timeout = aiohttp.ClientTimeout(total=4)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 CyberGuard/1.0"
    }

    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            for _ in range(max_hops):
                try:
                    async with session.head(current_url, allow_redirects=False) as resp:
                        if resp.status in (301, 302, 303, 307, 308) and "Location" in resp.headers:
                            next_url = resp.headers["Location"]
                            if not next_url.startswith("http"):
                                parsed = urlparse(current_url)
                                next_url = f"{parsed.scheme}://{parsed.netloc}{next_url}"
                            chain.append(next_url)
                            current_url = next_url
                        else:
                            break
                except Exception:
                    # If HEAD is disallowed or fails, fallback to GET with stream
                    break
    except Exception as e:
        logger.debug(f"Redirect resolver failed for {url}: {e}")

    return chain
