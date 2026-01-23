# Healthy - Backlog

This file tracks future features, improvements, and technical debt to be addressed.

---

## High Priority

### Email Verification for Registration
**Status:** Planned for when domain is set up
**Description:** Confirm user email addresses before allowing full access
**Requirements:**
- AWS SES (Simple Email Service) for sending emails
- Domain with proper DNS records (SPF, DKIM, DMARC)
- Verification token system in database
- Email templates for verification
**Flow:**
1. User registers → account created as "unverified"
2. Verification email sent with unique link (expires in 24h)
3. User clicks link → account verified
4. Unverified users see "Please verify your email" message

### SSL/HTTPS
**Status:** Blocked - needs domain
**Description:** Secure all traffic with SSL certificates
**Requirements:**
- Domain name pointing to Contabo server (62.171.163.23)
- Let's Encrypt certificate via Certbot
- Nginx HTTPS configuration

### Custom Domain
**Status:** Not started
**Description:** Set up proper domain instead of IP address
**Tasks:**
- Purchase/configure domain
- Point DNS to Contabo server
- Configure Nginx for domain
- Set up SSL certificate

---

## Medium Priority

### Report History & Comparison
**Status:** In progress (Phase 2 item)
**Description:** View past health reports and compare changes over time
**Features:**
- List of all past reports with dates
- Side-by-side comparison of two reports
- Highlight improvements/regressions

### CAPTCHA Handling for Multi-User (Production)
**Status:** Planned for Phase 2+
**Description:** Handle CAPTCHAs when users sync from web interface
**Options:**
- Option A: CAPTCHA Proxy - Show CAPTCHA to user in webapp
- Option B: 2captcha/Anti-Captcha service (~$2-3/1000)
- Option C: Session cookie storage

### Automatic Sync Scheduling
**Status:** Not started
**Description:** Periodically sync linked accounts automatically
**Features:**
- Background job scheduler (Celery or APScheduler)
- User-configurable sync frequency
- Notification when new results found

---

## Low Priority

### Mobile App (Phase 3)
**Status:** Future phase
**Description:** React Native mobile application
**Features:**
- Cross-platform (iOS/Android)
- Push notifications for new results
- Offline access to reports

### Monetization (Phase 3)
**Status:** Future phase
**Description:** Subscription-based revenue model
**Features:**
- Free tier: Basic features, limited syncs
- Premium tier: Unlimited syncs, AI analysis, export
- Stripe payment integration

### Data Export
**Status:** Not started
**Description:** Allow users to export their health data
**Formats:**
- PDF report
- CSV/Excel for biomarkers
- JSON for full data export

### Share with Doctor
**Status:** Not started
**Description:** Generate shareable links for healthcare providers
**Features:**
- Time-limited access links
- Select which data to share
- Track who accessed

---

## Technical Debt

### Regina Maria Headless Mode
**Priority:** Low
**Issue:** Site detects headless browser despite stealth measures
**Current workaround:** Falls back to visible browser
**Note:** Works fine for now, revisit when time permits

### Code Splitting
**Priority:** Low
**Issue:** Frontend bundle is >500KB
**Solution:** Implement dynamic imports and route-based code splitting

### Database Backups
**Priority:** Medium
**Issue:** No automated backup system
**Solution:** Set up pg_dump cron job, consider cloud backup

---

## Recently Completed

- [x] Document deletion with cascade delete of biomarkers
- [x] Upload progress UI with detailed AI analysis steps
- [x] PDF view icons in biomarkers and health reports
- [x] Fixed AI parser to handle longer PDFs (50k chars vs 4k)
- [x] Security fix: Documents filtered by user_id
- [x] JWT token expiration extended to 7 days
- [x] Edit linked account credentials
- [x] Biomarkers collapse by default, sort by issues

---

*Last updated: 2026-01-23*
