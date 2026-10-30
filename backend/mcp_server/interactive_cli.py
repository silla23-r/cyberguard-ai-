"""
Interactive CLI Tester for CyberGuard WhatsApp MCP Server.
Allows testing all MCP tools live with pre-built scam vectors or custom messages.
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


async def test_scenario(choice: str):
    if choice == "1":
        print("\n📥 Testing Saved Contact (Mom):")
        msg = "Hi beta, please remember to take your lunch. Call me when you are free."
        res = await analyze_incoming_whatsapp(
            sender_jid="+919811122233",
            message_body=msg,
            is_saved_contact=True,
            sender_name="Mom"
        )
        print(res)

    elif choice == "2":
        print("\n📥 Testing Unknown Sender (Fake Electricity Threat):")
        msg = (
            "Dear Customer, your electricity power will be disconnected tonight at 9:30 PM "
            "due to unpaid bill of Rs. 4,500. Immediately pay to bescom.bill@okaxis or call Mr. Sharma "
            "on +919876543210 to avoid permanent blackout. Linked Aadhaar: 9876 5432 1098."
        )
        res = await analyze_incoming_whatsapp(
            sender_jid="+919876543210",
            message_body=msg,
            is_saved_contact=False,
            sender_name="Unknown"
        )
        print(res)

    elif choice == "3":
        print("\n📥 Testing Unknown Sender (Digital Arrest Extortion):")
        msg = (
            "This is Cyber Crime Branch Mumbai. An illegal international parcel containing MDMA narcotics "
            "has been intercepted registered under your Aadhaar number. A non-bailable warrant has been issued. "
            "You are placed under Digital Arrest. Do not disconnect this call or our armed unit will arrive at your home."
        )
        res = await analyze_incoming_whatsapp(
            sender_jid="+919123456789",
            message_body=msg,
            is_saved_contact=False,
            sender_name="Police Officer"
        )
        print(res)

    elif choice == "4":
        print("\n📦 Inspecting Quarantine Inbox (Chats held safely away from user):")
        res = await get_quarantine_inbox()
        print(res)

    elif choice == "5":
        print("\n🛡️ Executing 1-Tap Permanent Block & 1930 Cyber Crime Report Generation:")
        res = await confirm_block_and_report(
            sender_jid="+919876543210",
            incident_summary="Electricity power cutoff extortion with fake Axis Bank VPA",
            file_1930_dossier=True
        )
        print(res)

    elif choice == "6":
        custom_text = input("\nEnter custom WhatsApp message to test: ")
        sender = input("Enter sender phone (e.g. +919876543210): ") or "+919876543210"
        is_saved = input("Is this a saved contact in address book? (y/n): ").lower() == 'y'
        res = await analyze_incoming_whatsapp(
            sender_jid=sender,
            message_body=custom_text,
            is_saved_contact=is_saved,
            sender_name="Custom"
        )
        print("\n🔍 CyberGuard MCP Analysis:")
        print(res)


async def main():
    while True:
        print("\n" + "=" * 65)
        print("🛡️  CYBERGUARD WHATSAPP MCP SERVER — INTERACTIVE TESTER")
        print("=" * 65)
        print("1. Test Message from Mom (Whitelisted contact -> Clean Pass)")
        print("2. Test Electricity Threat from Unknown Sender (Auto-Quarantine)")
        print("3. Test Digital Arrest Extortion Call/Text (Auto-Quarantine)")
        print("4. View Quarantine Inbox (Pending Guardian / User Review)")
        print("5. 1-Tap Permanent Block & Generate 1930 Legal PDF Dossier")
        print("6. Test Custom WhatsApp Message")
        print("0. Exit")
        print("=" * 65)

        choice = input("Select an option (0-6): ").strip()
        if choice == "0":
            print("Exiting...")
            break
        elif choice in ["1", "2", "3", "4", "5", "6"]:
            await test_scenario(choice)
        else:
            print("Invalid choice, please select 0-6.")


if __name__ == "__main__":
    asyncio.run(main())

