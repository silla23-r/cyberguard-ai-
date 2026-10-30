"""
Google Safe Browsing Threat Intelligence Tool.
Checks URLs against Google's constantly updated lists of unsafe web resources.
"""
import aiohttp
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

async def check_url_safebrowsing(api_key: str, target_url: str) -> Dict[str, Any]:
    """
    Queries Google Safe Browsing Lookup API v4.
    Returns matched threats (MALWARE, SOCIAL_ENGINEERING, UNWANTED_SOFTWARE).
    """
    result: Dict[str, Any] = {
        "is_threat": False,
        "threat_types": [],
        "scanned": False,
        "details": "No API key configured"
    }

    if not api_key or api_key.strip() == "your_google_safe_browsing_key_here":
        # Heuristic check fallback
        if target_url.endswith(".apk") or "free-recharge" in target_url:
            result["is_threat"] = True
            result["threat_types"] = ["MALWARE_HEURISTIC"]
            result["scanned"] = True
            result["details"] = "Heuristic match on high-risk APK / fraud pattern"
        return result

    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key.strip()}"
    
    payload = {
        "client": {
            "clientId": "cyberguard-ai",
            "clientVersion": "1.0.0"
        },
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": target_url}]
        }
    }

    try:
        timeout = aiohttp.ClientTimeout(total=4)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(endpoint, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    matches = data.get("matches", [])
                    result["scanned"] = True
                    if matches:
                        result["is_threat"] = True
                        result["threat_types"] = [m.get("threatType") for m in matches]
                        result["details"] = f"Safe Browsing flagged as {', '.join(result['threat_types'])}"
                    else:
                        result["details"] = "URL not found on Google blacklist"
                else:
                    result["details"] = f"Safe Browsing API returned {resp.status}"
    except Exception as e:
        logger.warning(f"Safe Browsing lookup error: {e}")
        result["details"] = f"Error: {e}"

    return result

