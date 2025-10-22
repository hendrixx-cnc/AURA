# Compression Scenario Results

| Scenario | Method | Original Bytes | Encoded Bytes | Ratio (orig/encoded) | Round-trip |
|---|---|---:|---:|---:|---|
| Human → AI | template | 33 | 28 | 1.18 | ✅ |
| AI → AI (access) | template | 37 | 17 | 2.18 | ✅ |
| AI → AI (instruction) | template | 52 | 45 | 1.16 | ✅ |
| Human → AI (status) | plain | 50 | 50 | 1.00 | ✅ |
> **Compliance Note:** In production deployments the server immediately decompresses incoming payloads to plaintext and logs them for audit visibility, so only the wire format remains binary.

## Integration Summary (2025-10-22 13:03)

- Client↔Server harness: 16 conversational turns plus 10 AI-to-AI templates, **all pass**, avg AI-to-AI ratio **2.59 : 1**, human overall **1.32 : 1**, zero data loss, audit logged in `audit/integration_test.log`.
- Streaming harness (912 messages across 80 concurrent links with short conversations): avg latency **2.19 ms** (min 1.34 ms, max 4.51 ms, P95 3.32 ms), compression **1.42 : 1** (17,934 bytes saved), zero failures, audits in `audit/stream_*.log`.
- Latest discovery replay (`scripts/replay_audit_logs.py`): processed **7218** audit messages this session; no new templates promoted (coverage remains sufficient).

