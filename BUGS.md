# Bug Tracker

**Last Updated:** 2026-02-10

---

## Active Bugs

*No active bugs at this time.*

---

## Recently Resolved

### BUG-001: Biomarker Count Mismatch
**Resolved:** 2026-02-02 | **Severity:** Low (Cosmetic)

Dashboard showed 731 biomarkers, Biomarkers page showed 231. Fixed by updating `/dashboard/stats` to count unique biomarkers by canonical name.

### BUG-002: Doctor AI Not Working
**Resolved:** 2026-02-02 | **Severity:** High

Vault was locked after server restart. Fix: Vault must be manually unlocked after every server restart.

### BUG-003: Screenings Page Has No History
**Resolved:** 2026-02-02 | **Severity:** Medium

JSON strings in encrypted blob were double-serialized. Fixed parsing in `get_report_content()`.

### BUG-004: Profile Save Fails
**Resolved:** 2026-02-02 | **Severity:** High

`scan_profile_from_documents` was writing to unencrypted fields. Fixed to use vault encryption.

---

## Security Fixes (2026-02-10)

### SEC-001: Payment Verify Endpoint
**Severity:** Critical | **Status:** FIXED

`/payment/verify/{order_id}` now requires authentication and verifies user ownership.

### SEC-002: Password Reset Rate Limiting
**Severity:** High | **Status:** FIXED

Added rate limiting to `/forgot-password`, `/reset-password`, `/reset-password-with-recovery`, and `/check-reset-token` endpoints.

### SEC-003: Test Endpoint Protection
**Severity:** High | **Status:** FIXED

`/payment/simulate-success` now defaults to production mode (blocked unless ENVIRONMENT=development/test).

---

## Post-Server-Restart Checklist

After every server restart (`systemctl restart healthy-api`), you MUST:

```bash
# Unlock the vault
curl -X POST https://analize.online/api/admin/vault/unlock \
  -H "Content-Type: application/json" \
  -d '{"master_password": "YOUR_MASTER_PASSWORD"}'
```

---

## How to Report Bugs

1. Check if bug already exists in this file
2. Add to "Active Bugs" section with:
   - Unique ID (BUG-XXX)
   - Date reported
   - Severity (Critical/High/Medium/Low)
   - Description and steps to reproduce
   - Root cause (if known)
3. Move to "Recently Resolved" when fixed

---

*For auto-detected bugs from tests, see `backend_v2/tests/bug_reporter.py`*
