# Healthy - Active Tasks

## In Progress

(Nothing currently in progress)

---

## Pending

### Admin - Sync Schedule Visualization
**Status:** Pending
**Priority:** Medium

The sync schedule section in Admin doesn't show when the next cron jobs will run:
- [ ] Display next scheduled run time for each sync type
- [ ] Show countdown or timestamp until next run
- [ ] Visual timeline/calendar of scheduled syncs
- [ ] Current schedule intervals (daily, weekly, etc.)

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

### Admin Dashboard Enhancements
**Status:** Pending
**Priority:** Medium
- [ ] Server metrics (CPU, RAM, disk)
- [ ] Error logs viewer

### Gap Analysis - Future Enhancements
**Status:** Pending
**Priority:** Low

- [ ] Track when tests were last done
- [ ] Notifications when screenings are due

### Biomarkers - Group Same Tests Together
**Status:** Pending
**Priority:** Medium

In the Biomarkers section, group identical biomarkers together even if they have slightly different names:
- [ ] Normalize test names (e.g., "Hemoglobină", "Hemoglobina", "HGB" should be same)
- [ ] Show history inline when grouped
- [ ] Handle Romanian/English name variations
- [ ] AI-based name matching for similar tests

### Report History & Comparison
**Status:** Pending
**Priority:** Medium
- [ ] List all past reports
- [ ] Compare two reports side-by-side

### Separate Recommended Screenings Page
**Status:** Pending
**Priority:** Medium

Gap Analysis / Recommended Screenings should be a separate page/section, not just inside Health Reports.

### Database Backups
**Status:** Pending
**Priority:** Medium
- [ ] pg_dump cron job
- [ ] Cloud backup solution

---

## Completed

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
- [x] AI Reports - Data age awareness and trend considerations
- [x] Page refresh 404 fix - nginx config updated
- [x] Documents - Patient column and filter with rescan feature
- [x] Mobile Navigation - Burger menu with sliding drawer
- [x] Localization - Romanian default with full RO/EN translations
- [x] AI Responses - Bilingual & Language-Aware
- [x] AI Responses - Persistence to database
- [x] AI Reports - Include Personal Profile Data

---

*Last updated: 2026-01-25*
