"""
Automated Verification Test for CyberGuard WhatsApp MCP Server.
Tests tool invocation directly and verifies quarantine, whitelisting, and block/report flows.
"""
import sys
import json
import asyncio
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Fix Windows cp1252 stdout encoding
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server.server import (
    analyze_incoming_whatsapp,
    quarantine_chat,
    confirm_block_and_report,
    get_quarantine_inbox,
    release_quarantined_chat,
    configure_guardian_shield
)
from mcp_server.state_store import store


async def run_mcp_suite():
    print("=" * 70)
    print("CYBERGUARD WHATSAPP MCP SERVER — INTEGRATION SUITE")
    print("=" * 70)

    # Test 1: Whitelisted Contact (Should NOT be blocked or quarantined)
    print("\n[1/5] Testing Whitelisted Contact Protection...")
    res1_raw = await analyze_incoming_whatsapp(
        sender_jid="+919811122233",
        message_body="Hi beta, what time are you coming home today?",
        is_saved_contact=True,
        sender_name="Mom"
    )
    res1 = json.loads(res1_raw)
    assert res1["status"] == "SAFE_WHITELISTED"
    assert res1["risk_score"] == 0
    assert res1["decision"] == "ALLOW_DIRECT_DELIVERY"
    print("   PASS: Saved contact cleanly bypassed without false-positive alarms.")

    # Test 2: High-Risk Unknown Sender (Fake Electricity Threat with PII)
    print("\n[2/5] Testing Unknown Fraudster Ingestion & Auto-Quarantine...")
    scam_msg = (
        "Dear Consumer, your electricity power will be disconnected tonight at 9:30 PM. "
        "Pay unpaid bill of Rs. 4,500 immediately to bescom.bill@okaxis or call Mr. Sharma on +919876543210. "
        "Linked Aadhaar: 9876 5432 1098."
    )
    res2_raw = await analyze_incoming_whatsapp(
        sender_jid="+919876543210",
        message_body=scam_msg,
        is_saved_contact=False,
        sender_name="Unknown"
    )
    res2 = json.loads(res2_raw)
    assert res2["action"] == "QUARANTINE_MUTED", f"Unexpected action: {res2['action']}"
    assert res2["is_quarantined"] is True
    assert res2["pii_redacted_count"] >= 1, "PII was not redacted!"
    assert len(res2["evidence_sha256"]) == 64
    print(f"   PASS: High-risk message detected (Score: {res2['risk_score']}/100, Archetype: {res2['scam_archetype']}).")
    print(f"   PASS: Chat automatically quarantined, audio muted, and {res2['pii_redacted_count']} PII fields masked.")

    # Test 3: Check Quarantine Inbox
    print("\n[3/5] Testing Quarantine Inbox Retrieval...")
    inbox_raw = await get_quarantine_inbox()
    inbox = json.loads(inbox_raw)
    assert inbox["total_quarantined"] >= 1
    print(f"   PASS: Quarantine inbox contains {inbox['total_quarantined']} quarantined scam threads.")

    # Test 4: 1-Tap Permanent Block & Section 65B 1930 Dossier
    print("\n[4/5] Testing 1-Tap Permanent Block & 1930 Cybercrime Dossier Generation...")
    block_raw = await confirm_block_and_report(
        sender_jid="+919876543210",
        incident_summary="Electricity power cutoff extortion demand with fake Axis VPA",
        file_1930_dossier=True
    )
    block_res = json.loads(block_raw)
    assert block_res["status"] == "SENDER_PERMANENTLY_BLOCKED"
    assert block_res["section_65b_certified"] is True
    assert block_res["1930_dossier_url"] is not None
    print(f"   PASS: Fraudster blocked. 1930 dossier generated: {block_res['1930_dossier_url']}")
    print(f"   PASS: Tamper-proof verification URL: {block_res['verification_endpoint']}")

    # Test 5: Configure Guardian Shield Settings
    print("\n[5/5] Testing Guardian Shield Configuration...")
    config_raw = await configure_guardian_shield(
        enabled=True,
        guardian_phone="+919988776655",
        auto_quarantine_unknown=True
    )
    config = json.loads(config_raw)
    assert config["status"] == "GUARDIAN_CONFIG_UPDATED"
    assert config["config"]["guardian_phone"] == "+919988776655"
    print("   PASS: Guardian shield successfully updated for elderly protection.")

    print("\n" + "=" * 70)
    print("ALL 5 WHATSAPP MCP SERVER TESTS PASSED PERFECTLY!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_mcp_suite())

