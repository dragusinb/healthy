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


### Admin - Sync Scheduler Visual Improvements
**Status:** Pending
**Priority:** Medium

The sync scheduler section in Admin doesn't clearly show when the next cron jobs will run. Need better visual representation.

**Requirements:**
- [ ] Show clearly when each cron job will next run (exact time/date)
- [ ] Visual timeline or countdown for upcoming jobs
- [ ] Use more screen space - current layout is too compact
- [ ] Display all scheduled sync types with their next run times
- [ ] Consider a calendar/timeline view showing upcoming 24-48 hours
- [ ] Make it easy to see at a glance "what runs next and when"

**Nice to have:**
- Color coding by job type
- Click to manually trigger a job
- History of recent job runs with status (success/fail)

**Files to check:**
- `frontend_v2/src/pages/Admin.tsx` or similar admin components
- `backend_v2/routers/` - scheduler/admin endpoints
- Check what scheduler data is already available from API

### Gap Analysis - Future Enhancements
**Status:** Pending
**Priority:** Low

- [ ] Track when tests were last done
- [ ] Notifications when screenings are due

### Biomarkers - Fix Incorrect Grouping (AI Matching Accuracy)
**Status:** Pending
**Priority:** High

**Bug:** Biomarkers are being incorrectly grouped together based on partial name matches.

**Example of incorrect grouping:**
- "Concentratia medie a hemoglobinei eritrocitare (MCHC)" is NOT the same as "Hemoglobina (HGB)"
- These are different biomarkers that share the word "hemoglobin" but measure different things

**Requirements:**
- [ ] Same biomarkers MUST be grouped together (e.g., "Hemoglobina (HGB)" from different tests)
- [ ] Different biomarkers MUST NOT be grouped even if they share similar words
- [ ] AI grouping should be accurate - not too aggressive (wrong matches) and not too conservative (missing valid matches)
- [ ] Consider using abbreviations in parentheses (MCHC, HGB, etc.) as primary identifiers
- [ ] Consider using standardized biomarker codes (LOINC) if available

**Files to check:**
- Backend AI parsing/grouping logic
- `backend_v2/services/` - biomarker extraction and normalization
- Check AI prompts for biomarker matching

### AI Health Reports - Dynamic Specialist Selection from Generalist
**Status:** Pending
**Priority:** High

**Problem:** The list of specialists is currently a predefined dict. It should be dynamically determined by the generalist AI analysis.

**New Architecture:**
1. **Generalist AI call** should analyze all biomarkers and return:
   - General health assessment
   - A list of recommended specialists (as structured output)
   - Reasoning for each specialist recommendation

2. **For each recommended specialist**, make a separate AI call with:
   - Full biomarker data with dates/timeline clearly marked
   - Patient profile (age, height, weight, gender, medical history)
   - Clear instruction that recent results should carry more weight
   - Context that they should respond as a medical professional

**Prompt Requirements:**
- [ ] Update generalist prompt to output structured list of specialists needed
- [ ] Remove hardcoded specialist dict/list
- [ ] Create dynamic specialist prompt that receives full context
- [ ] Include timeline awareness in all prompts (dates of each biomarker)
- [ ] Instruct AI to prioritize recent results over older ones
- [ ] Pass complete patient profile to each specialist
- [ ] Specialists should act as medical professionals, not just data analyzers

**Example generalist output:**
```json
{
  "summary": "...",
  "recommended_specialists": ["cardiologist", "endocrinologist"],
  "reasoning": {
    "cardiologist": "Elevated LDL and triglycerides warrant cardiovascular review",
    "endocrinologist": "HbA1c trending upward over past 6 months"
  }
}
```

**Files to check:**
- `backend_v2/services/` - AI report generation, specialist definitions
- Check current specialist dict/enum and remove
- Update API to handle dynamic specialist list

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
