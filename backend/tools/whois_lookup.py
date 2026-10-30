"""
WHOIS Domain Age and Registrar Forensic Lookup.
Detects newly minted domains (< 30 days old) frequently used in phishing campaigns.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_HAS_WHOIS = False
try:
    import whois
    _HAS_WHOIS = True
except ImportError:
    pass

def extract_domain(url_or_domain: str) -> str:
    """Extracts base host domain from full URL or host string."""
    if "://" in url_or_domain:
        parsed = urlparse(url_or_domain)
        host = parsed.netloc or parsed.path
    else:
        host = url_or_domain.split("/")[0]
    return host.split(":")[0].lower()

def lookup_domain_age(url_or_domain: str) -> Dict[str, Any]:
    """
    Performs WHOIS check to compute domain creation age in days.
    Returns structured age, registrar info, and suspicion score.
    """
    domain = extract_domain(url_or_domain)
    
    result: Dict[str, Any] = {
        "domain": domain,
        "domain_age_days": None,
        "registrar": None,
        "creation_date": None,
        "is_suspicious": False,
        "error": None
    }

    # Whitelist well-known legitimate high-traffic domains to avoid unnecessary lookups
    trusted_roots = ["google.com", "microsoft.com", "apple.com", "gov.in", "nic.in", "sbi.co.in", "hdfcbank.com"]
    if any(domain.endswith(t) for t in trusted_roots):
        result["domain_age_days"] = 5000
        result["registrar"] = "Verified Authority"
        result["is_suspicious"] = False
        return result

    if not _HAS_WHOIS:
        # Heuristic fallback if whois binary/module isn't active
        result["error"] = "whois module not installed, fallback mode active"
        return result

    try:
        w = whois.whois(domain)
        creation = w.creation_date
        
        # WHOIS sometimes returns list of dates
        if isinstance(creation, list):
            creation = creation[0]
            
        if creation and isinstance(creation, datetime):
            # Normalize to UTC
            now = datetime.now(timezone.utc)
            if creation.tzinfo is None:
                creation = creation.replace(tzinfo=timezone.utc)
            
            age_days = (now - creation).days
            result["domain_age_days"] = max(0, age_days)
            result["creation_date"] = creation.strftime("%Y-%m-%d")
            
            # Scammer threshold: < 30 days is extremely suspicious
            if age_days < 30:
                result["is_suspicious"] = True

        if w.registrar:
            result["registrar"] = str(w.registrar)

    except Exception as e:
        logger.debug(f"WHOIS lookup exception for {domain}: {e}")
        result["error"] = str(e)

    return result
