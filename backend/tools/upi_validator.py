"""
UPI Virtual Payment Address (VPA) Validator and Impersonation Detector.
Identifies suspicious personal handles pretending to be official corporate or utility merchants.
"""
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Standard Indian Bank VPA Handles
KNOWN_HANDLES = {
    "okhdfcbank": "HDFC Bank (Google Pay)",
    "okaxis": "Axis Bank (Google Pay)",
    "oksbi": "State Bank of India (Google Pay)",
    "okicici": "ICICI Bank (Google Pay)",
    "ybl": "Yes Bank (PhonePe)",
    "ibl": "ICICI Bank (PhonePe)",
    "axl": "Axis Bank (PhonePe)",
    "paytm": "Paytm Payments Bank",
    "apl": "Amazon Pay",
    "barodampay": "Bank of Baroda"
}

VPA_REGEX = re.compile(r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$")

def extract_vpas_from_text(text: str) -> List[str]:
    """Extracts UPI VPAs from OCR or message text."""
    if not text:
        return []
    words = text.replace("\n", " ").split(" ")
    vpas = []
    for w in words:
        clean = w.strip(".,;:()[]\"'")
        if "@" in clean and VPA_REGEX.match(clean):
            vpas.append(clean)
    return list(dict.fromkeys(vpas))

def validate_vpa(vpa: str, claimed_brand: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes VPA structure.
    Flags scenarios where a personal username (e.g. rohan9982@okaxis) is used
    while the scammer claims to be 'Electricity Board' or 'SBI KYC Helpdesk'.
    """
    result: Dict[str, Any] = {
        "vpa": vpa,
        "is_valid_format": bool(VPA_REGEX.match(vpa)),
        "handle": None,
        "username": None,
        "provider": "Unknown PSP",
        "is_suspicious": False,
        "reasons": []
    }

    if not result["is_valid_format"]:
        result["reasons"].append("Malformed UPI address syntax")
        return result

    username, handle = vpa.split("@", 1)
    result["username"] = username
    result["handle"] = handle.lower()
    result["provider"] = KNOWN_HANDLES.get(result["handle"], f"Custom PSP ({handle})")

    # Check for random digit personal usernames (typical mule accounts)
    if re.search(r"\d{4,}", username):
        result["reasons"].append("VPA username contains random numeric sequences typical of temporary mule accounts")

    # Impersonation check: Claiming to be official authority with a personal Google Pay / PhonePe handle
    official_keywords = ["electricity", "bsnl", "airtel", "jio", "tatapower", "bescom", "sbi", "hdfc", "incometax", "police"]
    claimed_lower = (claimed_brand or "").lower()

    if any(k in claimed_lower for k in official_keywords):
        # Official entities almost never use personal psp handles like @okaxis or @ybl for billing
        if result["handle"] in ["okhdfcbank", "okaxis", "oksbi", "okicici", "ybl", "ibl"]:
            result["is_suspicious"] = True
            result["reasons"].append(
                f"Scammer claims to represent '{claimed_brand}', but provided a personal retail consumer UPI handle (@{result['handle']})"
            )

    return result

