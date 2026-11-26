"""
Generates harmless synthetic mock .apk archives inside backend/sample_inputs/
for safely testing and demonstrating CyberGuard AI's static APK Trojan Inspector
without storing or distributing any real executable malware.
"""
import io
import zipfile
from pathlib import Path


def build_mock_apk_bytes(
    package_name: str,
    permissions: list[str],
    extra_strings: list[str] | None = None,
    encode_utf16: bool = True,
) -> bytes:
    """Constructs a minimal valid ZIP-based mock APK archive in memory."""
    manifest_lines = [
        f'<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{package_name}">',
    ]
    for perm in permissions:
        manifest_lines.append(f'  <uses-permission android:name="android.permission.{perm}" />')
    manifest_lines.append("</manifest>")

    manifest_str = "\n".join(manifest_lines)
    manifest_bytes = (
        manifest_str.encode("utf-16le") if encode_utf16 else manifest_str.encode("utf-8")
    )

    dex_payload = b"dex\n035\x00SYNTHETIC_SAFE_MOCK_DEX\n" + "\n".join(extra_strings or []).encode("utf-8")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("AndroidManifest.xml", manifest_bytes)
        zf.writestr("classes.dex", dex_payload)
    return buf.getvalue()


SAMPLE_SPECS = [
    {
        "filename": "RTO_eChallan_Pay.apk",
        "package_name": "com.rto.echallan.update",
        "permissions": [
            "INTERNET",
            "READ_SMS",
            "RECEIVE_SMS",
            "SEND_SMS",
            "BIND_ACCESSIBILITY_SERVICE",
            "SYSTEM_ALERT_WINDOW",
            "REQUEST_INSTALL_PACKAGES",
        ],
        "extra_strings": [
            "com.sbi.lotusintouch",
            "com.phonepe.app",
            "https://rto-challan-verify.xyz/c2",
        ],
        "encode_utf16": True,
    },
    {
        "filename": "SBI_YONO_KYC_Update.apk",
        "package_name": "com.sbi.yono.kyc.update",
        "permissions": [
            "INTERNET",
            "READ_SMS",
            "RECEIVE_SMS",
            "READ_CALL_LOG",
            "BIND_ACCESSIBILITY_SERVICE",
            "RECEIVE_BOOT_COMPLETED",
        ],
        "extra_strings": [
            "com.sbi.lotusintouch",
            "com.sbi.SBIFreedomPlus",
            "com.snapwork.hdfc",
            "https://sbi-kyc-portal.top/otp",
        ],
        "encode_utf16": True,
    },
    {
        "filename": "PM_Kisan_Subsidy_Form.apk",
        "package_name": "gov.pmkisan.beneficiary.app",
        "permissions": [
            "INTERNET",
            "READ_SMS",
            "RECEIVE_SMS",
            "READ_CONTACTS",
            "SYSTEM_ALERT_WINDOW",
            "REQUEST_INSTALL_PACKAGES",
        ],
        "extra_strings": [
            "in.org.npci.upiapp",
            "com.google.android.apps.nbu.paisa.user",
            "https://api.telegram.org/bot_demo_c2/sendMessage",
        ],
        "encode_utf16": True,
    },
    {
        "filename": "FedEx_Parcel_Helper.apk",
        "package_name": "com.fedex.parcel.tracking",
        "permissions": [
            "INTERNET",
            "REQUEST_INSTALL_PACKAGES",
            "READ_CONTACTS",
            "CALL_PHONE",
        ],
        "extra_strings": [
            "Parcel Delivery Helper",
        ],
        "encode_utf16": False,
    },
    {
        "filename": "legit_calculator_sample.apk",
        "package_name": "com.example.calculator",
        "permissions": ["INTERNET"],
        "extra_strings": ["Simple Calculator Utility"],
        "encode_utf16": False,
    },
]


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    for spec in SAMPLE_SPECS:
        apk_bytes = build_mock_apk_bytes(
            package_name=spec["package_name"],
            permissions=spec["permissions"],
            extra_strings=spec["extra_strings"],
            encode_utf16=spec["encode_utf16"],
        )
        out_path = out_dir / spec["filename"]
        out_path.write_bytes(apk_bytes)
        print(f"Generated {out_path.name} ({len(apk_bytes)} bytes)")


if __name__ == "__main__":
    main()
