"""
VirusTotal Threat Intelligence Tool.
Integrates with VirusTotal v3 API to detect known malicious and phishing URLs.
"""
import base64
import aiohttp
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def scan_url_virustotal(api_key: str, target_url: str) -> Dict[str, Any]:
    """
    Queries VirusTotal v3 URL analysis endpoint.
    If API key is omitted, returns a graceful fallback status.
    """
    result: Dict[str, Any] = {
        "scanned": False,
        "malicious_count": 0,
        "suspicious_count": 0,
        "harmless_count": 0,
        "is_threat": False,
        "details": "No API key configured"
    }

    if not api_key or api_key.strip() == "your_virustotal_api_key_here":
        # Heuristic check for blatantly malicious patterns when VT key is absent
        suspicious_keywords = ["freemoney", "verify-bank", "kyc-update", "apk-download", "telegram-task"]
        if any(k in target_url.lower() for k in suspicious_keywords):
            result["scanned"] = True
            result["suspicious_count"] = 3
            result["is_threat"] = True
            result["details"] = "Heuristic match on high-risk keywords in URL path"
        return result

    try:
        # VirusTotal v3 requires URL identifier to be base64url encoded without padding
        url_id = base64.urlsafe_b64encode(target_url.encode()).decode().strip("=")
        endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        
        headers = {"x-apikey": api_key.strip()}
        timeout = aiohttp.ClientTimeout(total=5)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(endpoint, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                    result["scanned"] = True
                    result["malicious_count"] = stats.get("malicious", 0)
                    result["suspicious_count"] = stats.get("suspicious", 0)
                    result["harmless_count"] = stats.get("harmless", 0)
                    result["is_threat"] = (result["malicious_count"] > 0 or result["suspicious_count"] >= 2)
                    result["details"] = f"VT flags: {result['malicious_count']} malicious, {result['suspicious_count']} suspicious"
                else:
                    result["details"] = f"VirusTotal returned status {resp.status}"
    except Exception as e:
        logger.warning(f"VirusTotal lookup error: {e}")
        result["details"] = f"Lookup error: {e}"

    return result

