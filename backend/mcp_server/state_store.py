"""
In-Memory and Persistent State Store for CyberGuard WhatsApp MCP Server.
Tracks quarantined chats, whitelisted contacts, guardian settings, and blocked fraudsters.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Set, Optional

class QuarantineStore:
    def __init__(self):
        # sender_jid -> QuarantineRecord
        self.quarantined_chats: Dict[str, Dict[str, Any]] = {}
        # Blocked numbers
        self.blocked_senders: Set[str] = set()
        # Whitelisted contacts (saved address book)
        self.whitelisted_contacts: Set[str] = {
            "mom", "dad", "family", "office", "home"
        }
        # Guardian mode configuration
        self.guardian_config: Dict[str, Any] = {
            "enabled": True,
            "guardian_phone": "+919876500000",
            "auto_quarantine_unknown_high_risk": True,
            "strict_elderly_mode": True
        }

    def is_whitelisted(self, sender: str) -> bool:
        norm = sender.lower().strip()
        return norm in self.whitelisted_contacts or any(c in norm for c in ["mom", "dad", "sister", "brother"])

    def add_quarantine(
        self,
        sender_jid: str,
        reason: str,
        risk_score: int,
        message_snippet: str,
        evidence_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        record = {
            "sender_jid": sender_jid,
            "quarantined_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "reason": reason,
            "risk_score": risk_score,
            "message_snippet": message_snippet[:120],
            "evidence_hash": evidence_hash,
            "status": "QUARANTINED_MUTED",
            "actions_available": ["confirm_block_and_report", "release_quarantined_chat"]
        }
        self.quarantined_chats[sender_jid] = record
        return record

    def release_chat(self, sender_jid: str) -> bool:
        if sender_jid in self.quarantined_chats:
            del self.quarantined_chats[sender_jid]
            return True
        return False

    def block_sender(self, sender_jid: str) -> bool:
        self.blocked_senders.add(sender_jid)
        if sender_jid in self.quarantined_chats:
            self.quarantined_chats[sender_jid]["status"] = "PERMANENTLY_BLOCKED"
        return True

    def get_all_quarantined(self) -> List[Dict[str, Any]]:
        return list(self.quarantined_chats.values())

store = QuarantineStore()

