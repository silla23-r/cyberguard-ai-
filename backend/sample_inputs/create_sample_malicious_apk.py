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


def main() -> None:
    out_dir = Path(__file__).resolve().parent

    malicious_apk = build_mock_apk_bytes(
        package_name="com.rto.echallan.update",
        permissions=[
            "INTERNET",
            "READ_SMS",
            "RECEIVE_SMS",
            "SEND_SMS",
            "BIND_ACCESSIBILITY_SERVICE",
            "SYSTEM_ALERT_WINDOW",
            "REQUEST_INSTALL_PACKAGES",
        ],
        extra_strings=[
            "com.sbi.lotusintouch",
            "com.phonepe.app",
            "https://rto-challan-verify.xyz/c2",
        ],
        encode_utf16=True,
    )
    malicious_path = out_dir / "RTO_eChallan_Pay.apk"
    malicious_path.write_bytes(malicious_apk)

    safe_apk = build_mock_apk_bytes(
        package_name="com.example.calculator",
        permissions=["INTERNET"],
        extra_strings=["Simple Calculator Utility"],
        encode_utf16=False,
    )
    safe_path = out_dir / "legit_calculator_sample.apk"
    safe_path.write_bytes(safe_apk)

    print(f"Created safe mock malicious demo APK: {malicious_path}")
    print(f"Created clean baseline demo APK:      {safe_path}")


if __name__ == "__main__":
    main()
