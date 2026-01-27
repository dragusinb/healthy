# Healthy - Active Tasks

## In Progress

### MEGA TASK: Comprehensive App Testing & Bug Cleanup
**Status:** In Progress
**Priority:** HIGHEST
**Started:** 2026-01-26

**Objective:** Identify all user flows, create comprehensive tests, and clean up logical bugs.

#### Phase 1: User Flow Identification
Document all user journeys through the application:

**Authentication Flows:**
- [x] User registration (email/password) - tested with validation
- [x] User login (email/password) - tested with rate limiting
- [ ] Google OAuth login - needs manual testing
- [ ] Password reset flow - not implemented
- [x] Session management (token expiration, refresh) - 1-day expiration

**Profile Management:**
- [x] View profile - tested
- [x] Edit profile (name, gender, height, weight, blood type) - tested with validation
- [ ] Auto-save functionality - needs frontend testing
- [ ] Profile scan from documents - needs manual testing
- [x] Medical history (allergies, conditions, medications) - tested

**Provider Account Flows:**
- [ ] Add linked account (Regina Maria, Synevo)
- [ ] Edit linked account credentials
- [ ] Delete linked account
- [ ] Manual sync trigger
- [ ] View sync status/history
- [ ] Error handling (wrong password, CAPTCHA, site down)

**Document Management:**
- [x] View documents list - tested (auth required)
- [ ] Filter documents by patient/source/date - needs frontend testing
- [x] Download document - tested (security validated)
- [x] Upload document manually - tested (size limit, PDF only)
- [x] Delete document - tested (auth required)
- [x] View document biomarkers - tested (auth required)
- [ ] Re-process document - needs manual testing

**Biomarkers & Health Data:**
- [ ] View biomarkers list
- [ ] Search/filter biomarkers
- [ ] View biomarker evolution (chart)
- [ ] View out-of-range alerts
- [ ] Biomarker grouping by category

**AI Health Reports:**
- [ ] Generate new report
- [ ] View report history
- [ ] Compare reports
- [ ] Specialist referrals

**Screenings/Gap Analysis:**
- [ ] View recommended screenings
- [ ] Track overdue tests
- [ ] Mark tests as completed

**Admin Panel (Admin users only):**
- [ ] View all users
- [ ] View sync jobs
- [ ] Trigger manual syncs
- [ ] View server stats
- [ ] View error logs
- [ ] Manage biomarker mappings
- [ ] Database backups

#### Phase 2: Test Implementation
Create automated tests for each flow:

- [ ] Backend unit tests (pytest)
- [ ] Backend integration tests
- [ ] API endpoint tests
- [ ] Frontend component tests
- [ ] End-to-end tests (Playwright)

#### Phase 3: Bug Identification & Fixes
Find and fix logical bugs:

- [ ] Data consistency issues
- [ ] Edge case handling
- [ ] Error message clarity
- [ ] UI/UX issues
- [ ] Performance bottlenecks

#### Progress Notes:
- 2026-01-26: Initial setup - pytest framework, live API smoke tests created
- 2026-01-27: Added comprehensive test suites (84 tests total, all passing)
  - Authentication flows (registration, login, tokens)
  - Profile management (CRUD, validation, isolation)
  - Document security (access control, download protection)
- 2026-01-27: Security hardening implemented (rate limiting, bcrypt, file limits)
- 2026-01-27: **BUG FIX** - Profile auto-save failing (422 error) - empty strings sent as height/weight instead of null
- 2026-01-27: Extended test suites (119 tests total, all passing)
  - Added linked accounts tests (provider account management)
  - Added biomarkers/dashboard tests (stats, filtering, evolution)
  - Added health reports tests (reports, specialists, gap analysis)
  - Fixed bcrypt compatibility (passlib → direct bcrypt usage)
  - Added test mode bypass for rate limiting

---

## Pending

### Security Hardening (From Bug Sweep)
**Status:** Mostly Complete
**Priority:** Medium (remaining items)

**Fixed (2026-01-26):**
- [x] Remove hardcoded default credentials (only seed in dev mode)
- [x] Fix path traversal vulnerability in document download
- [x] Add proper exception handling (remove bare except handlers)
- [x] Add input validation for height/weight
- [x] Add email validation in registration (EmailStr)
- [x] Add password minimum length (6 chars)
- [x] Improve encryption key derivation (configurable salt)

**Fixed (2026-01-27):**
- [x] Add rate limiting on auth endpoints (5 attempts/5min, 15min lockout)
- [x] Upgrade password hashing to bcrypt
- [x] Reduce token expiration from 7 days to 1 day
- [x] Add file upload size limits (20MB max, PDF only)

**Remaining (Medium Priority):**
- [ ] Implement CSRF protection
- [ ] Fix race condition in sync tracking (add proper locking)
- [ ] Add JSON validation for array fields
- [ ] Enforce HTTPS in production (needs domain + SSL cert)

### Testing Infrastructure
**Status:** Initial Setup Complete
**Priority:** Medium

Implemented:
- [x] Unit test framework (pytest in backend_v2/tests/)
- [x] Live API smoke tests (test_live_api.py)
- [x] Test authentication flows
- [x] Test protected endpoints require auth
- [x] Test input validation

Remaining:
- [ ] Add more comprehensive unit tests
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Add frontend testing (React Testing Library)
- [ ] Set up staging environment

### Regina Maria CAPTCHA Bypass Improvement
**Status:** Working ✓
**Priority:** Low (maintenance only)

Current behavior: Headless mode triggers reCAPTCHA, auto-solves using 2captcha/anti-captcha service.

Implemented:
- [x] CAPTCHA solving service integration (2captcha, Anti-Captcha)
- [x] Auto-solve reCAPTCHA v2 during login
- [x] Fallback between services if one fails
- [x] Rate limiting (max 3 attempts per sync to control costs)
- [x] Improved token injection with DOM event dispatching
- [x] CAPTCHA type detection (visible vs invisible)
- [x] Diagnostic screenshots for troubleshooting

Potential future improvements:
- [ ] Better stealth techniques (user-agent, viewport, webdriver flags)
- [ ] Session/cookie persistence between syncs

### Multi-Patient Account Handling (Future Enhancement)
**Status:** Pending
**Priority:** Low

Remaining feature:
- [ ] Allow user to select whose documents to import during sync (requires UI for patient selection)

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
- [x] Auto-retry sync after user updates credentials


### Gap Analysis - Future Enhancements
**Status:** In Progress
**Priority:** Low

- [x] Track when tests were last done - Shows "X months ago" or "Never done" on each screening
- [x] Highlight overdue tests based on recommended frequency
- [ ] Notifications when screenings are due (requires push notification infrastructure)

### Database Backups
**Status:** Pending
**Priority:** Medium
- [x] pg_dump cron job (daily at 3 AM, 7-day retention)
- [ ] Cloud backup solution (AWS S3 or similar)
- [x] Admin endpoint to view/create backups

---

## Completed

- [x] Security Bug Sweep & Fixes - Path traversal fix, input validation, email validation, exception handling
- [x] CAPTCHA Auto-Solve Integration - 2captcha/anti-captcha service integration, rate limiting, improved token injection
- [x] Testing Infrastructure Setup - pytest tests, live API smoke tests
- [x] Screenings - Track When Tests Were Last Done - Shows "X months ago" or "Never done", highlights overdue tests based on frequency
- [x] Multi-Patient Detection & Warning - Detect multiple patients in documents, warn on profile scan, dashboard endpoint for patient info
- [x] Admin - Remove Redundant Service Status Section - Removed old Service Status section (was buggy and redundant with Server Stats), cleaned up frontend/backend code
- [x] Admin - Service Status Fix - Updated endpoint to use correct service name (healthy-api), disabled old duplicate service
- [x] Auto-retry sync after user updates credentials - When credentials are updated for an ERROR account, automatically trigger sync
- [x] Conturi Conectate - Page Error Fix - Fixed null error_type handling that caused translation lookup errors
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

*Last updated: 2026-01-27*
