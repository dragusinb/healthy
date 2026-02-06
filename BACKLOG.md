# Healthy - Backlog

This file tracks future features, improvements, and technical debt.

---

## Phase Status & Missing Items

### Phase 0: MVP - COMPLETE ✓
All items done.

### Phase 1: Biomarker Extraction - COMPLETE ✓
All items done.

### Phase 2: Multi-User & AI Analysis - 95% Complete
**Missing:**
- [ ] Email verification (blocked - needs domain + AWS SES)
- [ ] Report history comparison (side-by-side view)

### Phase 3: Monetization & Mobile - NOT STARTED
**Missing (all):**
- [ ] Subscription tiers (Free/Premium)
- [ ] Stripe payment integration
- [ ] React Native mobile app
- [ ] Push notifications
- [ ] Offline access
- [ ] Share reports with doctors

### Phase 4: Production Deployment - 40% Complete
**Done:**
- [x] PostgreSQL database
- [x] Contabo VPS deployment
- [x] Nginx reverse proxy
- [x] Systemd services

**Missing:**
- [ ] Custom domain
- [ ] SSL/HTTPS (Let's Encrypt)
- [ ] GDPR compliance documentation
- [ ] Automated database backups
- [ ] Monitoring and alerting
- [ ] Load balancing (if needed)

---

## High Priority - New Requirements

### Crawling Polish & Reliability
**Priority:** HIGH
**Status:** Not started
**Problems to solve:**
1. Interrupted syncs leave documents in limbo state
2. No automatic retry for failed syncs
3. Users must manually trigger sync

**Solutions needed:**
- Add sync status tracking (pending, in_progress, completed, failed)
- Implement retry logic for failed syncs
- Add "stuck sync" detection and auto-recovery
- Clean up partial/limbo documents on failure

### Automatic Periodic Sync (Cron System)
**Priority:** HIGH
**Status:** Not started
**Description:** Automatically check linked accounts for new documents
**Requirements:**
- Background job scheduler (APScheduler or Celery)
- Configurable sync frequency per account (daily/weekly)
- Rate limiting to avoid overloading server
- Queue system to handle multiple users
- Sync only when new documents likely (check last sync date)
**Considerations:**
- Don't sync all users at once (stagger)
- Skip accounts that recently failed
- Respect server resources (max concurrent syncs)

### Localization (Romanian Default)
**Priority:** HIGH
**Status:** Not started
**Description:** Full app translation with Romanian as default
**Scope:**
- All UI text (buttons, labels, messages)
- Error messages
- Health report content (AI responses)
- Email templates (when implemented)
**Implementation:**
- i18next or react-intl for frontend
- Language selector in settings
- Store preference per user
- Romanian: default, English: secondary

### Admin Dashboard
**Priority:** HIGH
**Status:** Not started
**Description:** Monitor server health and user activity
**Features:**
- Server metrics (CPU, RAM, disk usage)
- Active users count
- Sync status overview (running, queued, failed)
- Error logs viewer
- Document processing queue
- Database stats (users, documents, biomarkers)
- Manual controls (restart sync, clear queue)
**Access:** Restricted to admin users only

---

## Medium Priority

### Email Verification for Registration
**Status:** Blocked - needs domain + AWS SES
**Flow:**
1. User registers → account created as "unverified"
2. Verification email sent with unique link
3. User clicks link → account verified
4. Unverified users see "Please verify your email"

### SSL/HTTPS
**Status:** Blocked - needs domain
**Requirements:**
- Domain pointing to 62.171.163.23
- Let's Encrypt via Certbot
- Auto-renewal cron job

### Report History & Comparison
**Status:** Planned
**Features:**
- List all past reports
- Compare two reports side-by-side
- Highlight improvements/regressions

### CAPTCHA Handling for Production
**Status:** Planned
**Options:**
- Show CAPTCHA to user in webapp (proxy approach)
- 2captcha service as fallback

---

## Low Priority

### Mobile App (Phase 3)
React Native app with push notifications

### Monetization (Phase 3)
Stripe integration, subscription tiers

### Data Export
PDF reports, CSV export, JSON full export

### Share with Doctor
Time-limited shareable links

---

## Technical Debt

### Regina Maria Headless Detection
**Priority:** Low
**Workaround:** Falls back to visible browser

### Frontend Bundle Size
**Priority:** Low
**Status:** DONE ✓
**Issue:** >500KB bundle (was 1080KB)
**Solution:** Code splitting with React.lazy() - reduced to 432KB main bundle

### Database Backups
**Priority:** Medium
**Status:** DONE ✓
**Solution:** pg_dump cron job running daily at 3 AM, keeps 7 days of backups
**Location:** /opt/healthy/backups/

---

## Infrastructure Resources

### Current Server (Contabo VPS)
- **IP:** 62.171.163.23
- **OS:** Ubuntu
- **Resources:** Check with `htop`, `df -h`
- **Services running:**
  - healthy-api (uvicorn)
  - xvfb (virtual display for crawlers)
  - nginx (reverse proxy)
  - postgresql

### Resource Considerations
- **Crawlers:** Each Playwright browser uses ~200-500MB RAM
- **AI Parsing:** OpenAI API calls (external, no local resources)
- **Max concurrent syncs:** Recommend 2-3 max to avoid OOM
- **Database:** PostgreSQL, lightweight for current scale

### Monitoring Commands
```bash
# Check server resources
ssh root@62.171.163.23 "htop"  # or top
ssh root@62.171.163.23 "df -h"  # disk space
ssh root@62.171.163.23 "free -h"  # memory

# Check services
ssh root@62.171.163.23 "systemctl status healthy-api"
ssh root@62.171.163.23 "systemctl status postgresql"

# Check logs
ssh root@62.171.163.23 "journalctl -u healthy-api -n 100"

# Database stats
ssh root@62.171.163.23 "PGPASSWORD=HealthyDB123 psql -h localhost -U healthy -d healthy -c 'SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM documents; SELECT COUNT(*) FROM test_results;'"
```

---

## Recently Completed

- [x] Document deletion with cascade delete
- [x] Upload progress UI with AI analysis steps
- [x] PDF view icons in biomarkers and health reports
- [x] Fixed AI parser for longer PDFs (50k chars)
- [x] Security fix: Documents filtered by user_id
- [x] JWT token expiration extended to 7 days
- [x] Edit linked account credentials
- [x] Biomarkers collapse by default, sort by issues
- [x] Created BACKLOG.md for tracking

---

*Last updated: 2026-01-23*
