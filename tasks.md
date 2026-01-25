# Healthy - Active Tasks

## In Progress

(None currently)

---

## Pending

### Conturi Conectate - Page Error & Human-Readable Errors
**Status:** In Progress
**Priority:** High

When entering "Conturi conectate" (Connected Accounts) page, an error is displayed.

**Issues:**
- [x] Add loading spinner and error handling to page
- [x] Human-readable error messages displayed (not stack traces)
- [ ] Fix the root cause of the error (need user to check browser console)

**Progress:**
- Added loading state with spinner
- Added proper error catch and display
- Error messages now show user-friendly text in current language

**Next steps:**
- Check browser console for specific JavaScript errors when page loads
- May be a database migration issue if error_type/error_acknowledged columns missing

### Multi-Patient Account Handling
**Status:** Pending
**Priority:** Medium

When a linked provider account has access to multiple patients (e.g., family members), the system should:
- [ ] Detect when documents belong to different patients (by name/CNP)
- [ ] Allow user to select whose documents to import
- [ ] Warn when profile scan finds mismatched patient names

### Provider Access Lost - User Notifications
**Status:** Mostly Done
**Priority:** Low

**Completed:**
- [x] Error types defined (wrong_password, captcha_failed, site_down, etc.)
- [x] Human-readable messages in RO/EN locale files
- [x] Error modal with icon, description, and actions
- [x] "Update credentials" flow from error modal
- [x] Error acknowledgement system
- [x] Dashboard notification banner for unacknowledged errors

**Optional Enhancements:**
- [ ] Email notification for critical errors
- [ ] Auto-retry sync after user updates credentials


### Gap Analysis - Future Enhancements
**Status:** Pending
**Priority:** Low

- [ ] Track when tests were last done
- [ ] Notifications when screenings are due

### Database Backups
**Status:** Pending
**Priority:** Medium
- [x] pg_dump cron job (daily at 3 AM, 7-day retention)
- [ ] Cloud backup solution (AWS S3 or similar)
- [x] Admin endpoint to view/create backups

---

## Completed

- [x] XServer/Xvfb Error Misclassification Fix - Added server_error category for display/browser errors, shows "Server Maintenance" message instead of wrong password
- [x] Biomarker Name Unification Across Suppliers - Added canonical_name column, normalize at import time, admin endpoints for mapping management and migration
- [x] Profile - Auto-Save Translation Fix & Age Extraction Improvement - Added missing translation keys (profile.saving, profile.autoSaveFailed) in RO/EN, improved AI prompt to prioritize header section for extracting patient age from Regina Maria documents
- [x] Profile Page - Button Size & Auto-Save - Removed Save button, implemented 1-second debounced auto-save, consistent button styling, save status indicator
- [x] Separate Recommended Screenings Page - New /screenings route, grouped tests by category, priority stats, profile-aware recommendations
- [x] Report History & Comparison - Session-based history view, comparison mode to select 2 reports, side-by-side comparison with risk change and stats
- [x] Admin - Sync Scheduler Visual Improvements - Live countdown timer for next job, color-coded job cards with icons, expanded grid layout, highlighted next job, manual trigger buttons
- [x] AI Health Reports - Dynamic Specialist Selection - Generalist now outputs structured referrals with reasoning, specialist prompts enhanced to act as medical professionals, timeline-aware formatting
- [x] Biomarkers - Fix Incorrect Grouping (AI Matching Accuracy) - Fixed algorithm to prioritize parenthetical abbreviations, use word-boundary matching, sort variants by length
- [x] Profile - Fix "Scanează din documente" Button & Age Extraction - Smaller button with hidden text on mobile, age_years fallback for birth date extraction
- [x] AI Reports - Date Awareness & Specialist Triggering - Added infectious_disease specialist, 12-month filter for auto-triggering, generalist context passed to specialists
- [x] Biomarkers - Group Same Tests Together - Normalized names, grouped display with expandable history, trend indicators
- [x] Admin Dashboard Enhancements - Server metrics (CPU, RAM, disk gauges), Error logs viewer with expandable section
- [x] Admin - Sync Schedule Visualization - ScheduleVisual component shows 14-day history + 3-day future, Scheduler Jobs shows next run times
- [x] CRITICAL: Fix File Storage Isolation Bug - user-specific directories, migration, validation
- [x] Fix server - orphan process blocking port 8000
- [x] Update login text to "Toate analizele tale intr-un singur loc"
- [x] Create .env.production with correct API URL
- [x] Deploy frontend with HTTPS API URL
- [x] Profile extraction feature (backend + frontend)
- [x] Clear wrong profile data (Dumitru Niculescu) from user 1
- [x] Generate clean deployment package (5.77 MB)
- [x] Data Isolation Audit - All endpoints properly filter by user_id
- [x] Dashboard notification banner for provider errors
- [x] Gap Analysis persistence - saves to DB, loads on page refresh
- [x] Page refresh 404 fix - nginx config updated
- [x] Documents - Patient column and filter with rescan feature
- [x] Mobile Navigation - Burger menu with sliding drawer
- [x] Localization - Romanian default with full RO/EN translations
- [x] AI Responses - Bilingual & Language-Aware
- [x] AI Responses - Persistence to database
- [x] AI Reports - Include Personal Profile Data

---

*Last updated: 2026-01-25*
