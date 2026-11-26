"""
Static Android APK Trojan & Sideloading Forensic Inspector for CyberGuard AI.
Safely inspects uploaded .apk archives purely in memory using Python's built-in zipfile
without executing untrusted code, guarding against Zip Bombs and oversize payloads.
"""
import hashlib
import io
import logging
import re
import zipfile
from typing import List, Optional, Set

from models.schemas import ApkInspectionResult
from tools.url_analyzer import extract_urls_from_text

logger = logging.getLogger(__name__)

# Size limits for Zip-Bomb and OOM protection
MAX_APK_UPLOAD_BYTES = 25 * 1024 * 1024        # 25 MB max uploaded APK
MAX_MANIFEST_READ_BYTES = 5 * 1024 * 1024      # 5 MB max uncompressed AndroidManifest.xml
MAX_DEX_SCAN_BYTES = 3 * 1024 * 1024           # 3 MB max read per classes.dex chunk

SMS_PERMISSIONS: Set[str] = {
    "READ_SMS",
    "RECEIVE_SMS",
    "SEND_SMS",
    "RECEIVE_MMS",
    "READ_CALL_LOG",
    "PROCESS_OUTGOING_CALLS",
}

ACCESSIBILITY_PERMISSIONS: Set[str] = {
    "BIND_ACCESSIBILITY_SERVICE",
    "SYSTEM_ALERT_WINDOW",
    "WRITE_SETTINGS",
}

DROPPER_PERMISSIONS: Set[str] = {
    "REQUEST_INSTALL_PACKAGES",
    "RECEIVE_BOOT_COMPLETED",
    "READ_CONTACTS",
    "CALL_PHONE",
    "GET_ACCOUNTS",
}

ALL_FLAGGED_PERMISSIONS = SMS_PERMISSIONS | ACCESSIBILITY_PERMISSIONS | DROPPER_PERMISSIONS

TARGETED_BANK_PACKAGES = {
    "com.sbi.lotusintouch": "SBI YONO",
    "com.sbi.SBIFreedomPlus": "SBI YONO Lite",
    "com.phonepe.app": "PhonePe",
    "net.one97.paytm": "Paytm",
    "com.google.android.apps.nbu.paisa.user": "Google Pay",
    "in.org.npci.upiapp": "BHIM UPI",
    "com.csam.icici.bank.imobile": "ICICI iMobile",
    "com.snapwork.hdfc": "HDFC MobileBanking",
    "com.axis.mobile": "Axis Mobile",
}

BAIT_FILENAME_BRANDS = {
    "rto": "Traffic Police / RTO e-Challan",
    "challan": "Traffic Police / RTO e-Challan",
    "parivahan": "Parivahan Govt Portal",
    "sbi": "State Bank of India (YONO)",
    "yono": "State Bank of India (YONO)",
    "hdfc": "HDFC Bank",
    "icici": "ICICI Bank",
    "axis": "Axis Bank",
    "kisan": "PM-Kisan Govt Scheme",
    "electricity": "Electricity Board",
    "bescom": "State Electricity Board (BESCOM)",
    "kyc": "Bank KYC Verification",
    "fedex": "Courier / Customs Notice",
}

NOISY_XML_DOMAINS = (
    "schemas.android.com",
    "www.w3.org",
    "ns.adobe.com",
    "purl.org",
)


def _decode_binary_strings(raw_bytes: bytes) -> str:
    """
    Extracts searchable ASCII/UTF-8 and UTF-16LE strings from Android Binary XML (AXML)
    or DEX string pools without requiring heavy external parsers.
    """
    utf8_text = raw_bytes.decode("utf-8", errors="ignore")
    even_len = len(raw_bytes) - (len(raw_bytes) % 2)
    utf16_text = raw_bytes[:even_len].decode("utf-16le", errors="ignore")
    compact_text = raw_bytes.replace(b"\x00", b"").decode("utf-8", errors="ignore")
    return f"{utf8_text}\n{utf16_text}\n{compact_text}"


def _extract_package_name(manifest_text: str) -> Optional[str]:
    """Extracts the primary Android package identifier if present in manifest strings."""
    explicit = re.search(r'package\s*=\s*["\']([a-zA-Z0-9_.]+)["\']', manifest_text)
    if explicit:
        return explicit.group(1)

    # Heuristic lookup for reverse-DNS package identifiers inside AXML string pool
    ignored_prefixes = (
        "android.",
        "androidx.",
        "com.google.android.gms",
        "com.android.",
        "schemas.android.",
    )
    for match in re.findall(r"\b(?:com|in|org|net|gov)\.[a-z0-9_]+(?:\.[a-z0-9_]+)+\b", manifest_text):
        if not match.startswith(ignored_prefixes) and match not in TARGETED_BANK_PACKAGES:
            return match
    return None


def _filter_suspicious_urls(raw_urls: List[str]) -> List[str]:
    """Filters out standard XML namespace schemas from extracted APK strings."""
    cleaned: List[str] = []
    for url in raw_urls:
        lowered = url.lower()
        if any(noise in lowered for noise in NOISY_XML_DOMAINS):
            continue
        cleaned.append(url)
    return list(dict.fromkeys(cleaned))


def infer_apk_bait_brand(filename: Optional[str]) -> Optional[str]:
    """Identifies government/bank authority impersonated by a suspicious APK filename."""
    if not filename:
        return None
    name_lower = filename.lower()
    for keyword, label in BAIT_FILENAME_BRANDS.items():
        if keyword in name_lower:
            return label
    return None


def inspect_apk_bytes(apk_bytes: bytes, filename: str = "uploaded_app.apk") -> ApkInspectionResult:
    """
    Performs safe, in-memory static inspection of an uploaded Android .apk file.
    Detects OTP SMS theft permissions, Accessibility hijacking, and C2 endpoints.
    """
    size_bytes = len(apk_bytes)
    sha256_hex = hashlib.sha256(apk_bytes).hexdigest()

    result = ApkInspectionResult(
        is_valid_apk=False,
        filename=filename,
        sha256_hash=sha256_hex,
        file_size_bytes=size_bytes,
    )

    if size_bytes == 0:
        result.risk_flags.append("Uploaded APK file is empty.")
        return result

    if size_bytes > MAX_APK_UPLOAD_BYTES:
        result.risk_flags.append(
            f"Upload exceeds maximum safe static analysis threshold ({MAX_APK_UPLOAD_BYTES // (1024 * 1024)} MB)."
        )
        return result

    # Validate ZIP magic header (PK\x03\x04)
    if apk_bytes[:4] != b"PK\x03\x04":
        result.risk_flags.append("Invalid archive signature: File does not start with a valid APK/ZIP header.")
        return result

    try:
        with zipfile.ZipFile(io.BytesIO(apk_bytes), "r") as zf:
            names = zf.namelist()
            if "AndroidManifest.xml" not in names:
                result.risk_flags.append("Missing AndroidManifest.xml: Archive is not a valid Android application package.")
                return result

            result.is_valid_apk = True

            manifest_info = zf.getinfo("AndroidManifest.xml")
            if manifest_info.file_size > MAX_MANIFEST_READ_BYTES:
                result.risk_flags.append(
                    "Zip-Bomb guard triggered: Uncompressed AndroidManifest.xml exceeds 5 MB safety cap."
                )
                result.sideload_dropper_risk = True
                return result

            manifest_raw = zf.read("AndroidManifest.xml")
            manifest_text = _decode_binary_strings(manifest_raw)

            # Extract package identifier
            result.package_name = _extract_package_name(manifest_text)

            # Extract android.permission.* strings
            found_perms = re.findall(r"android\.permission\.([A-Z0-9_]+)", manifest_text)
            flagged_found = sorted({p for p in found_perms if p in ALL_FLAGGED_PERMISSIONS})
            result.dangerous_permissions = flagged_found

            if any(p in SMS_PERMISSIONS for p in flagged_found):
                result.sms_interception_risk = True
                result.risk_flags.append(
                    "SMS/OTP Interception Capability: App requests SMS/Call-Log access used to steal banking OTPs silently."
                )

            if any(p in ACCESSIBILITY_PERMISSIONS for p in flagged_found):
                result.accessibility_abuse_risk = True
                result.risk_flags.append(
                    "Screen Hijack Capability: App requests Accessibility/Overlay control used to read PINs or auto-authorize transfers."
                )

            if any(p in DROPPER_PERMISSIONS for p in flagged_found):
                result.sideload_dropper_risk = True
                result.risk_flags.append(
                    "Sideload Dropper / Persistence: App requests package installation or boot-persistence privileges."
                )

            # Inspect AndroidManifest and bounded DEX sections for C2 URLs & targeted banking apps
            corpus_chunks = [manifest_text]
            dex_files = [n for n in names if n.startswith("classes") and n.endswith(".dex")][:2]
            for dex_name in dex_files:
                dex_info = zf.getinfo(dex_name)
                if dex_info.file_size <= MAX_DEX_SCAN_BYTES * 3:
                    with zf.open(dex_name, "r") as dex_fp:
                        dex_sample = dex_fp.read(MAX_DEX_SCAN_BYTES)
                        corpus_chunks.append(_decode_binary_strings(dex_sample))

            full_corpus = "\n".join(corpus_chunks)

            # Detect references to major Indian banking / UPI apps
            targeted_banks: List[str] = []
            for pkg, app_label in TARGETED_BANK_PACKAGES.items():
                if pkg in full_corpus:
                    targeted_banks.append(f"{app_label} ({pkg})")
            if targeted_banks:
                result.targeted_banking_apps = targeted_banks
                result.risk_flags.append(
                    f"Targeted Financial Apps Referenced: {', '.join(targeted_banks)}"
                )

            # Extract suspicious C2 / Telegram bot URLs
            raw_urls = extract_urls_from_text(full_corpus)
            filtered_urls = _filter_suspicious_urls(raw_urls)
            if filtered_urls:
                result.embedded_urls = filtered_urls[:5]
                result.risk_flags.append(
                    f"Embedded Network Endpoints Found Inside APK: {', '.join(result.embedded_urls)}"
                )

            # Flag utility/bank bait filename combined with invasive permissions
            bait_brand = infer_apk_bait_brand(filename)
            if bait_brand and (result.sms_interception_risk or result.accessibility_abuse_risk):
                result.risk_flags.append(
                    f"Bait Impersonation Mismatch: APK pretends to be '{bait_brand}' while requesting invasive device/OTP controls."
                )

    except zipfile.BadZipFile:
        result.risk_flags.append("Corrupted or invalid APK archive format.")
    except Exception as exc:
        logger.warning(f"APK inspection error for {filename}: {exc}")
        result.risk_flags.append(f"Static inspection encountered an unexpected archive structure: {exc}")

    return result
