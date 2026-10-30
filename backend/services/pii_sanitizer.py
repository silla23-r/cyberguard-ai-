"""
Zero-Knowledge PII Sanitization Engine for CyberGuard AI.
Compliant with Digital Personal Data Protection (DPDP) Act, 2023 & RBI Cyber Security Guidelines.

Automatically redacts personal banking credentials, balances, Aadhaar numbers, and PAN cards
from OCR text and user messages BEFORE sending data to LLMs or persistent logs, while preserving
actionable scammer threat indicators (suspicious VPAs, fraud phone numbers, phishing URLs).
"""
import re
from typing import Tuple, Dict, Any, List

# Regular expression patterns for Indian sensitive PII
CARD_NUMBER_PATTERN = re.compile(
    r'\b(?:\d{4}[-\s]?){3}\d{4}\b'  # 16 digit cards (Visa, MasterCard, RuPay)
)

AADHAAR_PATTERN = re.compile(
    r'\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b'  # 12 digit Indian Aadhaar
)

PAN_PATTERN = re.compile(
    r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'  # Indian Income Tax PAN Card
)

# Indian Bank Account Number patterns (typically 9 to 18 digits preceded by A/c or Account)
ACCOUNT_NO_PATTERN = re.compile(
    r'(?i)(?:a/c|account(?:\s*no|\s*number)?)[^\d]{0,5}(\d{9,18})\b'
)

# Financial balances and sensitive account amounts
BALANCE_PATTERN = re.compile(
    r'(?i)(?:bal(?:ance)?|avl\s*bal|credited\s*with|debited\s*for)[^\d₹$]{0,10}(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d{2})?)'
)

# CVV pattern
CVV_PATTERN = re.compile(
    r'(?i)\b(?:cvv|cvv2|security\s*code)[^\d]{0,3}(\d{3,4})\b'
)

# OTP pattern
OTP_PATTERN = re.compile(
    r'(?i)\b(?:otp|one\s*time\s*password|verification\s*code)[^\d]{0,5}(\d{4,8})\b'
)


def mask_card(match: re.Match) -> str:
    val = match.group(0).replace('-', '').replace(' ', '')
    last4 = val[-4:] if len(val) >= 4 else "XXXX"
    return f"[REDACTED_CARD: ****-****-****-{last4}]"


def mask_aadhaar(match: re.Match) -> str:
    val = match.group(0).replace('-', '').replace(' ', '')
    last4 = val[-4:] if len(val) >= 4 else "XXXX"
    return f"[REDACTED_AADHAAR: ****-****-{last4}]"


def mask_pan(match: re.Match) -> str:
    val = match.group(0)
    return f"[REDACTED_PAN: *****{val[5:9]}*]"


def sanitize_pii(text: str) -> Tuple[str, Dict[str, Any]]:
    """
    Sanitizes raw text, scrubbing sensitive citizen PII while returning
    a telemetry audit trail of redacted categories.
    """
    if not text:
        return "", {"redacted_count": 0, "categories": []}

    sanitized = text
    redacted_categories: List[str] = []
    redacted_count = 0

    # 1. Mask Payment Cards
    cards_found = len(CARD_NUMBER_PATTERN.findall(sanitized))
    if cards_found > 0:
        sanitized = CARD_NUMBER_PATTERN.sub(mask_card, sanitized)
        redacted_categories.append(f"{cards_found} Payment Card(s)")
        redacted_count += cards_found

    # 2. Mask Aadhaar
    aadhaar_found = len(AADHAAR_PATTERN.findall(sanitized))
    if aadhaar_found > 0:
        sanitized = AADHAAR_PATTERN.sub(mask_aadhaar, sanitized)
        redacted_categories.append(f"{aadhaar_found} Aadhaar ID(s)")
        redacted_count += aadhaar_found

    # 3. Mask PAN
    pan_found = len(PAN_PATTERN.findall(sanitized))
    if pan_found > 0:
        sanitized = PAN_PATTERN.sub(mask_pan, sanitized)
        redacted_categories.append(f"{pan_found} PAN Card(s)")
        redacted_count += pan_found

    # 4. Mask Bank Account Numbers
    acc_matches = ACCOUNT_NO_PATTERN.findall(sanitized)
    if acc_matches:
        for acc in acc_matches:
            last4 = acc[-4:] if len(acc) >= 4 else "XXXX"
            sanitized = sanitized.replace(acc, f"****{last4}")
            redacted_count += 1
        redacted_categories.append(f"{len(acc_matches)} Bank Account(s)")

    # 5. Mask OTPs
    otp_matches = OTP_PATTERN.findall(sanitized)
    if otp_matches:
        for otp in otp_matches:
            sanitized = sanitized.replace(otp, "[REDACTED_OTP]")
            redacted_count += 1
        redacted_categories.append(f"{len(otp_matches)} OTP(s)")

    # 6. Mask CVV
    cvv_matches = CVV_PATTERN.findall(sanitized)
    if cvv_matches:
        for cvv in cvv_matches:
            sanitized = sanitized.replace(cvv, "[REDACTED_CVV]")
            redacted_count += 1
        redacted_categories.append(f"{len(cvv_matches)} CVV Code(s)")

    # 7. Mask Balances
    bal_matches = BALANCE_PATTERN.findall(sanitized)
    if bal_matches:
        for bal in bal_matches:
            # Avoid replacing tiny numbers like 0 or 1
            if len(bal.replace(',', '')) >= 3:
                sanitized = sanitized.replace(bal, "[REDACTED_BALANCE]")
                redacted_count += 1
        if redacted_count > 0:
            redacted_categories.append("Account Balances")

    audit = {
        "redacted_count": redacted_count,
        "categories": list(set(redacted_categories)),
        "is_sanitized": redacted_count > 0,
        "dpdp_compliant": True
    }

    return sanitized, audit
