# CyberGuard WhatsApp MCP (Model Context Protocol) Server

> **Enterprise-grade Autonomous WhatsApp Security Agent with "Quarantine & 1-Tap Interlock" Architecture.**
> Designed for Tier-1 placements, hackathons, and research viva presentations.

---

## 🏛️ Architecture & Protection Flow

```
[ Incoming WhatsApp Message ]
              │
              ▼
    [ analyze_incoming_whatsapp ]
    ├── 1. Contact Whitelist Check (Bypasses verified saved contacts)
    ├── 2. DPDP Zero-Knowledge PII Sanitization
    ├── 3. Adversarial Prompt Injection Defense
    ├── 4. UPI Intent & QR VPA Forensics
    ├── 5. Fresh Domain & WHOIS Threat Lookup
    └── 6. Multi-Factor Scam Scoring
              │
              ├── Score < 40  ──► Direct delivery to user
              └── Score >= 40 ──► 🚨 DANGER ADVISORY:
                                  • Auto-Mute notifications
                                  • Move chat to Quarantine Holding Area
                                  • Trigger 1-Tap Block & Section 65B Dossier
```

---

## 🛠️ MCP Tools Exposed

| Tool Name | Parameters | Purpose |
| :--- | :--- | :--- |
| `analyze_incoming_whatsapp` | `sender_jid`, `message_body`, `is_saved_contact`, `sender_name` | Analyzes threat score, strips PII, and outputs danger advisory. |
| `quarantine_chat` | `sender_jid`, `reason`, `risk_score` | Mutes and isolates suspicious conversations without alerting the scammer. |
| `confirm_block_and_report` | `sender_jid`, `incident_summary`, `file_1930_dossier` | **Permanently blocks the scammer**, generates official 1930 Cybercrime PDF, and seals cryptographic SHA-256 evidence. |
| `get_quarantine_inbox` | *None* | Retrieves all held chats for user or family guardian review. |
| `release_quarantined_chat` | `sender_jid` | Restores a false-positive chat back to inbox. |
| `configure_guardian_shield` | `enabled`, `guardian_phone`, `auto_quarantine_unknown` | Configures strict protection mode for elderly family members. |

---

## 📂 MCP Resources Exposed

* `cyberguard://quarantine/list`: Real-time JSON stream of quarantined threats.
* `cyberguard://security/status`: Active DPDP compliance and total blocked fraudster count.

---

## 🚀 How to Run & Connect

### 1. Interactive 1-Click Tester (Terminal)
Double-click `run_mcp_tester.bat` or run:
```bash
python backend/mcp_server/interactive_cli.py
```

### 2. Connect to Cursor IDE
Add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "cyberguard-whatsapp": {
      "command": "python",
      "args": ["backend/mcp_server/server.py"],
      "env": { "PYTHONIOENCODING": "utf-8" }
    }
  }
}
```

### 3. Connect to Claude Desktop
Add to `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "cyberguard-whatsapp": {
      "command": "python",
      "args": ["<FULL_PATH_TO_PROJECT>/backend/mcp_server/server.py"],
      "env": { "PYTHONIOENCODING": "utf-8" }
    }
  }
}
```

