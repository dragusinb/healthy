# Bug Tracker

## Active Bugs

### BUG-001: Biomarker Count Mismatch (NOT A BUG - By Design)
**Reported:** 2026-02-02
**Status:** Clarified - Working as Intended
**Severity:** Low (Cosmetic/UX)

**Description:**
Dashboard (Panou principal) shows 731 biomarkers, but Biomarkers page shows only 231.

**Root Cause:**
This is intentional design:
- Dashboard shows **total biomarker records** (731 individual test results across all documents)
- Biomarkers page shows **unique biomarker types** (231 grouped by canonical name)

**Example:** If you have 10 cholesterol tests over time, Dashboard counts 10, Biomarkers page counts 1 (grouped).

**Recommendation:** Consider adding clarifying text like "731 total test results" vs "231 unique biomarkers tracked".

---

### BUG-002: Doctor AI Not Working
**Reported:** 2026-02-02
**Status:** Investigating
**Severity:** High

**Description:**
Doctor AI feature does not work.

**Possible Causes:**
1. Vault is locked on server - biomarker decryption fails
2. OpenAI API key issue
3. HTTP error during API call

**Investigation Needed:**
- Check server logs for errors on POST /health/analyze
- Verify vault is unlocked
- Test OpenAI API key is valid

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

### BUG-003: Screenings Page Has No History - RESOLVED 2026-02-02
### BUG-004: Profile Save Fails - RESOLVED 2026-02-02

---

## Deployment Notes

Fixes need to be deployed to production server:
1. `backend_v2/routers/users.py` - scan_profile vault encryption
2. `backend_v2/routers/health.py` - JSON string parsing for encrypted reports
