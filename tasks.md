# Healthy - Active Tasks

## In Progress

### Mobile Navigation - Burger Menu
Adding hamburger menu for mobile devices.

---

## Pending

### Documents - Patient Column & Filter - DONE
**Status:** Completed

Added patient name to documents:
- [x] patient_name field in Document model
- [x] Extract patient name during AI parsing (from patient_info.full_name)
- [x] Display patient name badge in documents list
- [x] Patient filter dropdown when multiple patients exist
- [x] Database migration applied

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

### Localization - Romanian Default - DONE
**Status:** Already Implemented

- [x] i18n with react-i18next
- [x] Romanian as default (fallbackLng: 'ro')
- [x] Language saved to localStorage
- [x] Language toggle in Layout (globe icon)
- [x] Full RO/EN translations in locales/

### Admin Dashboard Enhancements
**Status:** Pending
**Priority:** Medium
- Server metrics (CPU, RAM, disk)
- Error logs viewer

### Gap Analysis / Recommended Screenings - DONE
**Status:** Already Implemented
**Priority:** High

**Already Done:**
- [x] Backend `/health/gap-analysis` endpoint
- [x] AI-generated recommended screenings list
- [x] Priority levels (high, medium, low)
- [x] UI section in Health Reports page
- [x] Uses user profile for context (age, gender, conditions)

**Future Enhancements:**
- [ ] Track when tests were last done
- [ ] Notifications when screenings are due

### AI Reports - Include Personal Profile Data - DONE
**Status:** Already Implemented

All AI specialist reports already include full profile context:
- [x] Age, gender, DOB
- [x] Height, weight, BMI
- [x] Blood type
- [x] Chronic conditions
- [x] Current medications
- [x] Allergies
- [x] Lifestyle factors (smoking, alcohol, activity)

Profile is passed to GeneralistAgent, SpecialistAgents, and GapAnalysisAgent.

### AI Reports - Consider Data Age/Evolution - DONE
**Status:** Completed

Enhanced AI prompts to consider data age:
- [x] Added data age summary at top of biomarker list
- [x] Warning when most recent data is >6 months old
- [x] Strong warning when data is >1 year old
- [x] Prompts instruct AI to focus on recent results
- [x] Prompts ask AI to note when abnormal values have normalized

### Biomarkers - Group Same Tests Together
**Status:** Pending
**Priority:** Medium

In the Biomarkers section, group identical biomarkers together even if they have slightly different names:
- Normalize test names (e.g., "Hemoglobină", "Hemoglobina", "HGB" should be same)
- Show history inline when grouped
- Handle Romanian/English name variations
- AI-based name matching for similar tests

### Report History & Comparison
**Status:** Pending
**Priority:** Medium
- List all past reports
- Compare two reports side-by-side

### Separate Recommended Screenings Page
**Status:** Pending
**Priority:** Medium

Gap Analysis / Recommended Screenings should be a separate page/section, not just inside Health Reports.

### AI Responses - Bilingual & Language-Aware - DONE
**Status:** Already Implemented

- [x] All AI agents inherit from HealthAgent with LANGUAGE_INSTRUCTIONS
- [x] Romanian: "IMPORTANT: You MUST respond entirely in Romanian..."
- [x] Language passed from user.language through all endpoints
- [x] GeneralistAgent, SpecialistAgent, GapAnalysisAgent all support language

### AI Responses - Persistence - DONE
**Status:** Completed

All AI-generated content is now saved to database:
- [x] Health Reports - saved to HealthReport table
- [x] Specialist reports - saved to HealthReport table
- [x] Gap Analysis results - now saved (added persistence + /gap-analysis/latest endpoint)
- [x] Frontend loads saved gap analysis on page load

### Page Refresh Shows 404 Error - FIXED
**Status:** Completed

Fixed nginx regex to only match API paths with trailing content:
- Changed: `^/(auth|users|...)(/|$)` → `^/(auth|users|...)/`
- Now `/biomarkers` → SPA, `/dashboard/stats` → API

### Mobile Navigation - Burger Menu
**Status:** Pending
**Priority:** High

On mobile devices, the left sidebar menu is not visible. Need to add:
- [ ] Hamburger menu icon in header on mobile
- [ ] Sliding drawer/overlay for mobile navigation
- [ ] Close menu when navigating to a page

### Database Backups
**Status:** Pending
**Priority:** Medium
- pg_dump cron job
- Cloud backup solution

---

## Completed

- [x] Fix server - orphan process blocking port 8000
- [x] Update login text to "Toate analizele tale intr-un singur loc"
- [x] Create .env.production with correct API URL
- [x] Deploy frontend with HTTPS API URL
- [x] Profile extraction feature already implemented (backend + frontend)
- [x] Clear wrong profile data (Dumitru Niculescu) from user 1
- [x] Generate clean deployment package (5.77 MB) - `deploy_package/healthy_deploy_20260124_175934.zip`
- [x] Data Isolation Audit - All endpoints properly filter by user_id. "Dumitru Niculescu" issue was due to linked account having family member's documents.
- [x] Dashboard notification banner for provider errors
- [x] Gap Analysis persistence - saves to DB, loads on page refresh
- [x] AI Reports - Data age awareness and trend considerations
- [x] Page refresh 404 fix - nginx config updated
- [x] Documents - Patient column and filter

---

*Last updated: 2026-01-24*
