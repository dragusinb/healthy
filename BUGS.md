# Bug Tracker

## Active Bugs

### BUG-001: Biomarker Count Mismatch
**Reported:** 2026-02-02
**Status:** FIXED
**Severity:** Low (Cosmetic/UX)

**Description:**
Dashboard (Panou principal) shows 731 biomarkers, but Biomarkers page shows only 231.

**Root Cause:**
Dashboard was counting total test records instead of unique biomarker types.

**Fix Applied:**
Updated `/dashboard/stats` endpoint to count unique biomarkers by canonical name, matching the Biomarkers page grouping.

---

### BUG-002: Doctor AI Not Working
**Reported:** 2026-02-02
**Status:** FIXED
**Severity:** High

**Description:**
Doctor AI feature does not work.

**Root Cause:**
The vault was locked on the production server. After the API service restart, the vault needs to be manually unlocked with the master password. When the vault is locked, biomarker decryption fails, causing the AI analysis to fail.

**Fix Applied:**
Unlocked the vault on production server. This is a recurring maintenance task - the vault must be unlocked after every server restart.

---

### BUG-003: Screenings Page Has No History
**Reported:** 2026-02-02
**Status:** FIXED
**Severity:** Medium

**Description:**
Screeninguri recomandate (Recommended Screenings) page shows no history.

**Root Cause:**
During data migration, health report `findings` and `recommendations` were stored as JSON strings inside the encrypted blob. When decrypted, the code expected lists but got strings like `"[{...}]"` instead of `[{...}]`.

**Fix Applied:**
Updated `get_report_content()` in `health.py` to parse JSON strings if findings/recommendations are strings instead of lists.

---

### BUG-004: Profile Save Fails
**Reported:** 2026-02-02
**Status:** FIXED
**Severity:** High

**Description:**
Profile page shows "salvare esuata" (save failed) error. Also, date_of_birth (data nasterii) is no longer displayed.

**Root Cause:**
The `scan_profile_from_documents` function was writing directly to legacy unencrypted fields (`user.full_name`, `user.date_of_birth`) instead of encrypted fields when vault is unlocked. This caused inconsistency with the rest of the system which expects encrypted data.

**Fix Applied:**
Updated `scan_profile_from_documents()` in `users.py` to use vault encryption when available, matching the behavior of `update_profile()`.

---

## Resolved Bugs

### BUG-001: Biomarker Count Mismatch - RESOLVED 2026-02-02
### BUG-002: Doctor AI Not Working - RESOLVED 2026-02-02
### BUG-003: Screenings Page Has No History - RESOLVED 2026-02-02
### BUG-004: Profile Save Fails - RESOLVED 2026-02-02

---

## Deployment Notes

All fixes deployed to production server on 2026-02-02:
1. `backend_v2/routers/users.py` - scan_profile vault encryption
2. `backend_v2/routers/health.py` - JSON string parsing for encrypted reports
3. Vault unlocked after server restart

**IMPORTANT**: After every server restart (systemctl restart healthy-api), the vault must be manually unlocked:
```bash
curl -X POST http://localhost:8000/admin/vault/unlock \
  -H "Content-Type: application/json" \
  -d '{"master_password": "YOUR_MASTER_PASSWORD"}'
```
