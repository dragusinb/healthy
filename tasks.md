# Healthy - Active Tasks

## In Progress

### Admin - Sync Schedule Visualization
**Status:** In Progress
**Priority:** Medium

---

## Pending

### Conturi Conectate - Page Error & Human-Readable Errors
**Status:** Pending
**Priority:** High

When entering "Conturi conectate" (Connected Accounts) page, an error is displayed.

**Issues:**
- [ ] Fix the bug causing the error - page should load without errors
- [ ] Make all error messages human-readable (not technical/stack traces)
- [ ] Ensure proper error handling with user-friendly messages in RO/EN

**Files to check:**
- `frontend_v2/src/pages/LinkedAccounts.tsx` (or similar)
- `backend_v2/routers/` - linked accounts endpoints
- Check API response handling and error states

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
**Priority:** High

In the Biomarkers page, biomarkers with the same name appear as separate rows. They should be grouped under one expandable entry.

**Current behavior:** 5 glucose readings = 5 separate "Glucose" rows

**Expected behavior:**
- [ ] Group biomarkers with identical names into a single collapsible row
- [ ] Show the most recent value on the collapsed row
- [ ] Click to expand and see all historical measurements for that biomarker
- [ ] Maintain existing filter/search functionality
- [ ] Keep HIGH/LOW status badges visible

**Future enhancement (separate task):**
- Normalize similar names (e.g., "Hemoglobină", "Hemoglobina", "HGB" → same group)

**Files to check:**
- `frontend_v2/src/pages/Biomarkers.tsx`
- `frontend_v2/src/components/` - biomarker components
- `backend_v2/routers/` - biomarker API endpoints

### AI Health Reports - Date Awareness & Specialist Triggering
**Status:** Pending
**Priority:** High

Multiple issues with AI health report generation:

**Bug 1: AI ignores biomarker dates**
- Report claims active Strep pyogenes infection based on old results
- Latest analysis shows no infection, but AI doesn't prioritize recent data
- AI should weigh recent biomarkers more heavily and note when data is old

**Bug 2: Specialist reports don't use generalist findings**
- Specialist AI agents should receive the generalist analysis as context
- Generalist identifies concerns → triggers relevant specialists
- Currently specialists may not be aware of generalist's findings

**Bug 3: Missing Infectious Disease specialist**
- Generalist recommends "consultă un medic infecționist" (infectious disease doctor)
- But there's no Infectious Disease AI specialist to generate that report
- Either add Infectologist specialist or map recommendation to existing specialist

**Files to check:**
- `backend_v2/services/` - AI report generation logic
- `backend_v2/routers/` - health report endpoints
- Check how biomarkers are passed to AI (with dates?)
- Check specialist triggering logic

### Profile - Fix "Scanează din documente" Button & Age Extraction
**Status:** Pending
**Priority:** Medium

Issues with the profile scan feature:
- [ ] Button "Scanează din documente" is too big - reduce size to match other UI elements
- [ ] Age/birth date extraction from documents not working correctly

**Files to check:**
- `frontend_v2/src/pages/Profile.tsx` - button styling
- `backend_v2/services/` - AI profile extraction logic

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
