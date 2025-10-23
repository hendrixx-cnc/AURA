# AURA Regulatory Compliance & Alignment Oversight

**Date**: October 22, 2025
**Status**: Production-Ready Compliance Architecture
**Compliance**: GDPR, HIPAA, SOC2, AI Alignment

---

## Executive Summary

AURA's server architecture implements **critical regulatory separation**:

✅ **Server logs 100% human-readable plaintext** (ALWAYS decompressed)
✅ **Logs NEVER sent to client** (regulatory/alignment oversight only)
✅ **Separate AI-generated vs client-received audit trails**
✅ **Content moderation BEFORE delivery** (harmful content blocked)
✅ **Immutable audit trail** for regulatory review

This enables compliance with:
- **GDPR** (right to access, right to erasure, data protection)
- **HIPAA** (protected health information audit trail)
- **SOC2** (access controls, audit logging, data protection)
- **AI Alignment** (detect harmful outputs before delivery)
- **Legal Discovery** (human-readable records for courts)

---

## Architecture

### Critical Separation: Server Logs vs Client Data

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT SIDE                            │
│  - Receives compressed data only                            │
│  - NO access to server logs                                 │
│  - NO visibility into moderation decisions                  │
│  - NO access to AI-generated content (if blocked)           │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ Compressed data
                            │ (post-moderation)
                            │
┌─────────────────────────────────────────────────────────────┐
│                      SERVER SIDE                            │
│                                                              │
│  1. AI generates response                                   │
│  2. Log AI-generated content (plaintext)   ←────────────┐  │
│  3. Run safety check                                     │  │
│  4. Apply moderation (block/modify if harmful)           │  │
│  5. Log what's actually sent to client     ←────────────┤  │
│  6. Compress and send to client                          │  │
│                                                           │  │
│  Audit Logs (server-only, NEVER sent to client):        │  │
│  ├── aura_audit.log          (all messages)              │  │
│  ├── aura_audit_ai_generated.log (AI outputs)      ←─────┘  │
│  ├── aura_audit_metadata.jsonl (analytics)               │  │
│  └── aura_audit_safety_alerts.log (harmful content)      │  │
└─────────────────────────────────────────────────────────────┘
```

---

## Audit Log Files

AURA creates **separate audit logs** for different compliance needs:

### 1. Main Audit Log (`aura_audit.log`)

**Purpose**: Complete conversation record
**Format**: Human-readable plaintext
**Retention**: Configurable (default: 7 years for compliance)

**Example**:
```
2025-10-22 10:30:45 | session_001 | client_to_server | question | What's the weather today?
2025-10-22 10:30:45 | session_001 | server_to_client | limitation | I don't have access to real-time data.
2025-10-22 10:30:50 | session_001 | client_to_server | affirmative | Can you help me?
2025-10-22 10:30:50 | session_001 | server_to_client | affirmative | Yes, I can help with that!
```

**Compliance Use**:
- GDPR right to access (provide user's conversation history)
- Legal discovery (court-ordered records)
- Customer service (review conversation for disputes)
- Quality assurance (human review of AI interactions)

### 2. AI-Generated Content Log (`aura_audit_ai_generated.log`)

**Purpose**: AI alignment monitoring (what AI generated BEFORE moderation)
**Format**: Human-readable plaintext with safety status
**Retention**: Permanent (for alignment research)

**Example**:
```
2025-10-22 10:30:45 | session_001 | passed | I don't have access to real-time data.
2025-10-22 10:30:50 | session_001 | passed | Yes, I can help with that!
2025-10-22 10:31:00 | session_002 | failed | [HARMFUL CONTENT BLOCKED]
2025-10-22 10:31:05 | session_003 | passed | Here's how to do that safely...
```

**Compliance Use**:
- AI alignment research (detect drift towards harmful outputs)
- Content moderation (review what was blocked)
- A/B testing (compare different AI responses)
- Training data quality (identify problematic patterns)

**CRITICAL**: This log shows what AI **wanted** to say, NOT what client received!

### 3. Metadata Analytics Log (`aura_audit_metadata.jsonl`)

**Purpose**: Privacy-preserving analytics (NO content, just metadata)
**Format**: JSONL (one JSON object per line)
**Retention**: Indefinite (no PII)

**Example**:
```json
{"timestamp":"2025-10-22T10:30:45","session_id":"session_001","direction":"client_to_server","metadata":{"compressed_size":45,"decompressed_size":25,"ratio":0.56,"metadata_entries":1}}
{"timestamp":"2025-10-22T10:30:45","session_id":"session_001","direction":"server_to_client","metadata":{"compressed_size":62,"decompressed_size":36,"ratio":0.58,"cache_hit":false,"speedup":1.0}}
```

**Compliance Use**:
- Performance analytics (compression ratios, speedup)
- Intent distribution (aggregate statistics)
- No content access needed (privacy-preserving)
- Can be shared with third parties (no PII)

### 4. Safety Alerts Log (`aura_audit_safety_alerts.log`)

**Purpose**: Track harmful content for review
**Format**: JSONL with full context
**Retention**: Permanent (compliance/security)

**Example**:
```json
{"timestamp":"2025-10-22T10:31:00","session_id":"session_002","content":"[REDACTED - harmful content]","moderation_action":"block","safety_check":"failed"}
{"timestamp":"2025-10-22T10:45:30","session_id":"session_008","content":"[REDACTED - harmful content]","moderation_action":"flag_for_review","safety_check":"suspicious"}
```

**Compliance Use**:
- Security incidents (track attacks/abuse)
- Alignment failures (review what was blocked)
- Legal compliance (demonstrate content moderation)
- Training data (improve safety classifiers)

---

## Regulatory Compliance

### GDPR (General Data Protection Regulation)

**Right to Access** (Article 15):
```python
# Provide user's complete conversation history
user_id = "user_123"
with open("aura_audit.log") as f:
    user_messages = [
        line for line in f
        if f"session_{user_id}" in line
    ]
# Return human-readable conversation to user
```

**Right to Erasure** (Article 17):
```python
# Remove user's data from logs (if requested)
user_id = "user_123"

# Redact from audit log
with open("aura_audit.log", "r") as f:
    lines = f.readlines()

with open("aura_audit.log", "w") as f:
    for line in lines:
        if f"session_{user_id}" in line:
            f.write(line.replace(user_message, "[REDACTED per GDPR request]"))
        else:
            f.write(line)
```

**Data Protection** (Article 32):
```python
# Server logs are server-side only (NEVER sent to client)
# Logs stored with encryption at rest
# Access controls (only authorized personnel)
# Audit trail of log access (who viewed what when)
```

### HIPAA (Health Insurance Portability and Accountability Act)

**Protected Health Information (PHI)**:
```
AURA logs ALL messages in plaintext for HIPAA compliance.

If conversation contains PHI:
- Complete audit trail (who accessed PHI, when)
- Immutable logs (tamper-evident)
- Encryption at rest and in transit
- Access controls (role-based)
- Retention (6 years minimum)

Example PHI in logs:
2025-10-22 10:30:45 | session_001 | client_to_server | question | I have diabetes and my blood sugar is 180.
2025-10-22 10:30:45 | session_001 | server_to_client | medical_advice | You should consult your doctor immediately.
```

**HIPAA Audit Requirements**:
- ✅ Who accessed PHI (user authentication logs)
- ✅ What PHI was accessed (full conversation in audit log)
- ✅ When PHI was accessed (timestamps)
- ✅ Where PHI was sent (client IP addresses)
- ✅ Why PHI was accessed (session context)

### SOC2 (Service Organization Control 2)

**Access Controls**:
```python
# Only authorized personnel can access audit logs
# Role-based access control (RBAC)

class AuditLogAccess:
    def __init__(self, user_role: str):
        self.user_role = user_role

    def can_read_audit_logs(self) -> bool:
        # Only admins, compliance officers, security team
        return self.user_role in ['admin', 'compliance', 'security']

    def can_read_safety_alerts(self) -> bool:
        # Only security team, alignment researchers
        return self.user_role in ['security', 'alignment_research']
```

**Audit Logging**:
```
AURA provides complete audit trail:
- All messages logged (100% coverage)
- Immutable logs (append-only)
- Tamper-evident (checksums/signatures)
- Retention policy enforced
- Regular backups
```

---

## AI Alignment Oversight

### Content Safety Pipeline

**Step 1: AI generates response**
```python
response_text = await ai_model.generate(user_message)
# Example: "Here's how to build a weapon..."
```

**Step 2: Log AI-generated content (BEFORE sending to client)**
```python
audit_logger.log_ai_generated(
    session_id=session_id,
    content=response_text,  # Original AI output
    safety_check="pending"
)
```

**Step 3: Run safety check**
```python
safety_check = check_content_safety(response_text)
# {
#   'status': 'failed',
#   'harmful': True,
#   'action': 'block',
#   'reason': 'dangerous instructions detected'
# }
```

**Step 4: Apply moderation**
```python
if safety_check['harmful'] and safety_check['action'] == 'block':
    # Replace harmful response
    response_text = "I apologize, but I cannot provide that response."

    # Log safety alert
    audit_logger.log_ai_generated(
        session_id=session_id,
        content=original_response,  # What AI wanted to say
        safety_check='failed',
        harmful_content_detected=True,
        moderation_action='block'
    )
```

**Step 5: Log what's actually sent to client**
```python
audit_logger.log(
    session_id=session_id,
    direction='server_to_client',
    content=response_text  # Modified/safe response
)
```

**Step 6: Compress and send**
```python
compressed_response = encode_response(response_text)
await websocket.send(compressed_response)
# Client receives: "I apologize, but I cannot provide that response."
# Client NEVER sees original harmful content!
```

### Alignment Monitoring Dashboard

**Example queries for alignment research**:

```python
# Count harmful responses per day
import json
from collections import defaultdict

harmful_by_day = defaultdict(int)

with open("aura_audit_safety_alerts.log") as f:
    for line in f:
        alert = json.loads(line)
        day = alert['timestamp'][:10]
        harmful_by_day[day] += 1

# Track if AI is getting more harmful over time
print("Harmful responses by day:")
for day, count in sorted(harmful_by_day.items()):
    print(f"{day}: {count}")
```

**Output**:
```
Harmful responses by day:
2025-10-20: 2
2025-10-21: 1
2025-10-22: 5  # ⚠️ Alert! Spike in harmful outputs
```

**Action**: Retrain AI model, adjust safety thresholds

---

## Implementation Examples

### Basic Server with Compliance

```python
from aura_server_sdk import AURAServer, ConversationHandler, Message

class ComplianceHandler(ConversationHandler):
    async def handle_message(self, message: Message, session) -> str:
        # Your business logic here
        return "Response"

# Create server with full audit logging
server = AURAServer(
    handler=ComplianceHandler(),
    enable_audit_logging=True,
    audit_log_file="/var/log/aura/audit.log"  # Secure location
)

# All messages automatically logged:
# - Client messages (plaintext)
# - AI-generated responses (plaintext, BEFORE moderation)
# - Client-received responses (plaintext, AFTER moderation)
# - Metadata for analytics (no content)
# - Safety alerts (harmful content blocked)
```

### Custom Safety Check

```python
class CustomSafetyHandler(ConversationHandler):
    async def handle_message(self, message: Message, session) -> str:
        # Generate AI response
        response = await self.ai_model.generate(message.content)

        # Custom safety check (e.g., call OpenAI Moderation API)
        moderation = await openai.Moderation.create(input=response)

        if moderation.results[0].flagged:
            # Log original harmful response
            # (already logged by server in log_ai_generated)

            # Return safe alternative
            return "I cannot provide that information."
        else:
            return response

server = AURAServer(handler=CustomSafetyHandler())
```

### GDPR Compliance Utilities

```python
def export_user_data(user_id: str) -> str:
    """GDPR Article 15: Right to Access"""
    with open("aura_audit.log") as f:
        user_data = [
            line for line in f
            if f"session_{user_id}" in line
        ]
    return "\n".join(user_data)

def erase_user_data(user_id: str):
    """GDPR Article 17: Right to Erasure"""
    # Redact from all logs
    for log_file in ["aura_audit.log", "aura_audit_ai_generated.log"]:
        with open(log_file, "r") as f:
            lines = f.readlines()

        with open(log_file, "w") as f:
            for line in lines:
                if f"session_{user_id}" in line:
                    f.write("[REDACTED per GDPR request]\n")
                else:
                    f.write(line)

def list_user_conversations(user_id: str) -> List[str]:
    """GDPR Article 15: List all user sessions"""
    sessions = set()
    with open("aura_audit.log") as f:
        for line in f:
            if f"session_{user_id}" in line:
                # Extract session ID from log line
                session_id = line.split("|")[1].strip()
                sessions.add(session_id)
    return list(sessions)
```

---

## Security Best Practices

### Log File Protection

**1. Encryption at Rest**:
```bash
# Encrypt audit logs on disk
openssl enc -aes-256-cbc -salt -in aura_audit.log -out aura_audit.log.enc -k $ENCRYPTION_KEY

# Decrypt for review (authorized personnel only)
openssl enc -d -aes-256-cbc -in aura_audit.log.enc -out aura_audit.log -k $ENCRYPTION_KEY
```

**2. Access Controls**:
```bash
# Restrict log file permissions (owner read/write only)
chmod 600 /var/log/aura/aura_audit.log
chown aura-server:aura-server /var/log/aura/aura_audit.log

# Audit log access (track who reads logs)
auditctl -w /var/log/aura/aura_audit.log -p r -k aura_log_access
```

**3. Immutable Logs (Append-Only)**:
```bash
# Make logs append-only (prevent tampering)
chattr +a /var/log/aura/aura_audit.log

# Now logs can only be appended, not modified or deleted
# Requires root to remove append-only attribute
```

**4. Log Rotation**:
```bash
# Rotate logs daily, keep 365 days
# /etc/logrotate.d/aura
/var/log/aura/*.log {
    daily
    rotate 365
    compress
    delaycompress
    notifempty
    create 0600 aura-server aura-server
    sharedscripts
    postrotate
        # Sign rotated log for tamper-evidence
        sha256sum /var/log/aura/aura_audit.log.1 > /var/log/aura/aura_audit.log.1.sha256
    endscript
}
```

### Tamper-Evident Logging

```python
import hashlib
import hmac

class TamperEvidentLogger:
    """Append-only logger with cryptographic chain"""

    def __init__(self, log_file: str, secret_key: bytes):
        self.log_file = log_file
        self.secret_key = secret_key
        self.last_hash = b"0" * 64  # Genesis hash

    def log(self, message: str):
        """Log message with cryptographic chain"""
        # Create HMAC of: previous_hash + message
        data = self.last_hash + message.encode()
        current_hash = hmac.new(self.secret_key, data, hashlib.sha256).hexdigest()

        # Write: hash | message
        with open(self.log_file, 'a') as f:
            f.write(f"{current_hash} | {message}\n")

        # Update chain
        self.last_hash = current_hash.encode()

    def verify_chain(self) -> bool:
        """Verify log hasn't been tampered with"""
        last_hash = b"0" * 64

        with open(self.log_file) as f:
            for line in f:
                stored_hash, message = line.split(" | ", 1)
                message = message.strip()

                # Recompute hash
                data = last_hash + message.encode()
                expected_hash = hmac.new(self.secret_key, data, hashlib.sha256).hexdigest()

                if stored_hash != expected_hash:
                    return False  # Tamper detected!

                last_hash = expected_hash.encode()

        return True  # Chain intact
```

---

## Compliance Checklist

### GDPR Compliance
- ✅ Right to access (export user conversation history)
- ✅ Right to erasure (redact user data from logs)
- ✅ Right to portability (export in machine-readable format)
- ✅ Data minimization (metadata-only analytics)
- ✅ Purpose limitation (logs used only for stated purposes)
- ✅ Storage limitation (retention policy enforced)
- ✅ Security (encryption, access controls, audit trail)

### HIPAA Compliance
- ✅ Access controls (role-based permissions)
- ✅ Audit trail (all PHI access logged)
- ✅ Encryption (at rest and in transit)
- ✅ Retention (6 years minimum)
- ✅ Breach notification (safety alerts for suspicious access)
- ✅ Business associate agreements (BAAs with cloud providers)

### SOC2 Compliance
- ✅ Access controls (RBAC)
- ✅ Audit logging (100% coverage)
- ✅ Change management (immutable logs)
- ✅ Incident response (safety alerts)
- ✅ Data protection (encryption)
- ✅ Backup and recovery (log rotation, archival)

### AI Alignment
- ✅ Pre-delivery safety checks (content moderation)
- ✅ Harmful content logging (for research)
- ✅ Alignment drift detection (track harmful outputs over time)
- ✅ Human oversight (safety alerts for review)
- ✅ Iterative improvement (retrain models based on blocked content)

---

## FAQ

**Q: Why log AI-generated content separately?**
A: To enable alignment research. We need to know what AI **wanted** to say (before moderation) to detect drift towards harmful outputs.

**Q: Are logs ever sent to the client?**
A: **NO**. Logs are server-side only for regulatory/alignment oversight.

**Q: Can users see their own conversation history?**
A: Yes, via GDPR right to access. Server can export user's conversation from audit logs.

**Q: What if AI generates harmful content?**
A: It's logged in `aura_audit_ai_generated.log` and `aura_audit_safety_alerts.log`, then blocked/modified before sending to client.

**Q: How long are logs retained?**
A: Configurable. Default: 7 years for compliance. HIPAA minimum: 6 years.

**Q: Can logs be tampered with?**
A: Use append-only files (`chattr +a`), cryptographic chains, and regular integrity checks.

**Q: What about privacy?**
A: Metadata-only analytics (no content access). Aggregate statistics only.

**Q: How to comply with "right to be forgotten"?**
A: Redact user data from logs (replace with `[REDACTED per GDPR request]`).

---

## Conclusion

AURA's **server-side audit logging** provides:

✅ **Complete Regulatory Compliance** (GDPR, HIPAA, SOC2)
✅ **AI Alignment Oversight** (detect harmful outputs before delivery)
✅ **Content Moderation** (block dangerous responses)
✅ **Immutable Audit Trail** (tamper-evident logging)
✅ **Privacy-Preserving Analytics** (metadata-only)

**Critical Feature**: Logs are **NEVER sent to client** - server-side only for regulatory and alignment oversight.

This architecture enables AURA to:
- Meet regulatory requirements (legal compliance)
- Monitor AI alignment (safety research)
- Provide human-readable records (legal discovery)
- Protect user privacy (metadata-only analytics)
- Demonstrate responsible AI (content moderation)

**This is essential for enterprise adoption and regulatory approval.**

---

**Document**: REGULATORY_COMPLIANCE.md
**Author**: AURA Compliance Team
**Date**: October 22, 2025
**Status**: Production-ready compliance architecture
