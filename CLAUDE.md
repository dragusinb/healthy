# Healthy Project - Guidelines for Claude

## Project Vision
**Healthy** is a multi-user commercial medical data aggregation platform. Users connect their medical provider accounts, and the system automatically downloads lab results, extracts biomarkers using AI, and provides health insights through specialist AI agents.

## Development Phases

### Phase 0: MVP - Single User Functional Product (CURRENT)
**Goal:** Working product for the developer's own accounts

**Outcomes:**
- [ ] Synevo crawler works reliably (login, download PDFs)
- [ ] Regina Maria crawler works reliably (login, handle reCAPTCHA smoothly, download PDFs)
- [ ] CAPTCHA handling integrated smoothly in sync flow (visible browser, user solves, continues)
- [ ] Basic document storage and management

**Tag:** `v0.1-mvp`

---

### Phase 1: Biomarker Extraction & Visualization
**Goal:** Extract and display biomarkers with history

**Outcomes:**
- [ ] AI correctly extracts biomarkers from PDFs (name, value, unit, reference range)
- [ ] Biomarkers stored with proper categorization
- [ ] Table view: All biomarkers with search/filter
- [ ] Chart view: Historical trends for each biomarker
- [ ] Flag out-of-range values (HIGH/LOW)
- [ ] Dashboard with health summary

**Tag:** `v0.2-biomarkers`

---

### Phase 2: Multi-User & AI Health Analysis
**Goal:** Open registration + AI-powered health insights

**Outcomes:**
- [ ] User registration and authentication
- [ ] Secure credential storage (encrypted)
- [ ] AI Generalist Agent: Reviews full health history, identifies concerns
- [ ] AI Specialist Agents: Cardiologist, Endocrinologist, Hematologist, etc.
- [ ] Health Report generation with findings and recommendations
- [ ] Report history and comparison

**Tag:** `v0.3-ai-analysis`

---

### Phase 3: Monetization & Mobile App
**Goal:** Revenue model + cross-platform access

**Outcomes:**
- [ ] Subscription tiers (Free/Premium)
- [ ] Payment integration (Stripe)
- [ ] React Native mobile app
- [ ] Push notifications for new results
- [ ] Offline access to reports
- [ ] Share reports with doctors

**Tag:** `v0.4-mobile`

---

### Phase 4: Production Deployment
**Goal:** Live, scalable, secure production system

**Outcomes:**
- [ ] PostgreSQL database (production)
- [ ] Cloud deployment (AWS/GCP/Azure)
- [ ] SSL/HTTPS
- [ ] GDPR compliance
- [ ] Backup and disaster recovery
- [ ] Monitoring and alerting
- [ ] Load balancing

**Tag:** `v1.0-production`

---

## Roles & Responsibilities

### AI Agents (Phase 2+)

| Agent | Role | Triggers |
|-------|------|----------|
| **Generalist** | Initial evaluation, identifies areas of concern | After every sync |
| **Cardiologist** | Heart health, cholesterol, blood pressure markers | Lipid panel abnormalities |
| **Endocrinologist** | Hormones, thyroid, diabetes markers | Glucose, HbA1c, thyroid abnormalities |
| **Hematologist** | Blood cells, anemia, clotting | CBC abnormalities |
| **Hepatologist** | Liver function | Liver enzyme abnormalities |
| **Nephrologist** | Kidney function | Creatinine, BUN abnormalities |

### System Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend API | FastAPI | REST API, business logic |
| Frontend Web | React + Vite | Web interface |
| Frontend Mobile | React Native | Mobile apps (Phase 3) |
| Database | SQLite → PostgreSQL | Data storage |
| Crawlers | Playwright | Browser automation |
| AI Parsing | OpenAI GPT-4o | Document extraction |
| AI Analysis | OpenAI GPT-4o | Health analysis |

---

## Core Principles

### 1. User Experience First
- Clear feedback during long operations
- Mobile-friendly design

### CAPTCHA Strategy (by Phase)

**Phase 0 (MVP - Local):**
- Browser opens locally, user solves CAPTCHA manually
- Works for developer testing

**Phase 2+ (Multi-user - Web):**
- Option A: **CAPTCHA Proxy** - Detect CAPTCHA, show it to user in webapp iframe, forward solution back
- Option B: **CAPTCHA Service** - Use 2captcha/Anti-Captcha API (~$2-3/1000 solves)
- Option C: **Session Cookies** - User logs in manually once, we store session cookies
- **Recommended:** Option A for user control, Option B as fallback for automation

### 2. Security & Privacy
- Encrypt stored credentials
- HTTPS everywhere
- GDPR compliant
- User owns their data

#### Encryption Vault (IMPLEMENTED)
**All sensitive data is encrypted with a master password using AES-256-GCM. Keys are held in memory only - lost on server restart.**

**Encrypted data:**
- Provider login credentials (Regina Maria, Synevo usernames/passwords)
- Medical documents (PDF files)
- Biomarker values and test results
- Health reports content
- User profile PII (name, DOB, gender, etc.)

**Security model:**
- Master password required after every server restart
- PBKDF2 key derivation (600,000 iterations, SHA-256)
- AES-256-GCM authenticated encryption
- Unique nonce per encryption operation
- No keys ever written to disk

**Vault Operations:**

```bash
# Initialize vault (first time only)
curl -X POST https://analize.online/api/admin/vault/initialize \
  -H "Content-Type: application/json" \
  -d '{"master_password": "YOUR-16-CHAR-PASSWORD"}'

# Unlock vault (after every server restart)
curl -X POST https://analize.online/api/admin/vault/unlock \
  -H "Content-Type: application/json" \
  -d '{"master_password": "YOUR-16-CHAR-PASSWORD"}'

# Check vault status
curl https://analize.online/api/admin/vault/status

# Lock vault (optional - clears keys from memory)
curl -X POST https://analize.online/api/admin/vault/lock
```

**When vault is locked:**
- All encrypted data inaccessible (returns 503 error)
- Sync jobs skip execution
- Frontend shows vault unlock prompt
- Admin panel shows vault status indicator

**Recovery:** There is NO password recovery. If password is forgotten, all encrypted data is permanently lost.

See `VAULT_IMPLEMENTATION.md` for detailed implementation notes.

**Goal:** The system administrator (even with database access) should NOT be able to:
- Read any user's medical documents
- See biomarker values
- Access provider credentials
- Connect to a user's medical provider accounts

### 3. Reliability
- Multiple download fallback methods
- Graceful error handling
- Retry logic for transient failures

### 4. Hardware Awareness
**Be mindful of server resources - don't overload the machine.**

Current limits implemented:
- `MAX_CONCURRENT_SYNCS = 2` - Only 2 provider syncs can run simultaneously
- `MAX_CONCURRENT_DOCUMENT_PROCESSING = 3` - Only 3 documents processed at once
- Scheduler intervals: Sync check every 30 min, document processing every 2 min, cleanup every 1 hour
- Consecutive failure limit: 5 failures before disabling auto-sync for an account
- Stuck sync timeout: 1 hour before marking as failed

When adding new background jobs or concurrent operations:
- Always implement concurrency limits
- Use tracking sets to prevent duplicate operations
- Add timeouts and cleanup mechanisms
- Consider the Contabo VPS has limited RAM/CPU
- Test with realistic load before deploying

### 5. Maintainability
- Clean code, clear separation of concerns
- Document progress in log.md
- Tag releases in git

---

## Git Workflow

```bash
# Feature development
git checkout -b feature/feature-name
# ... make changes ...
git commit -m "Description"
git push origin feature/feature-name

# After phase completion
git tag -a v0.X-name -m "Phase X complete"
git push origin --tags
```

**Repository:** GitHub (configured with token)
**Main branch:** `main`

---

## File Structure
```
Healthy/
├── backend_v2/          # FastAPI backend
│   ├── main.py          # App entry point
│   ├── models.py        # SQLAlchemy models
│   ├── routers/         # API endpoints
│   └── services/        # Crawlers, AI, business logic
├── frontend_v2/         # React frontend
├── data/raw/            # Downloaded PDFs (gitignored)
├── log.md               # Development progress log
├── CLAUDE.md            # This file - project guidelines
└── PLAN.md              # Detailed implementation plan
```

---

## Session Workflow
1. Read `log.md` and `CLAUDE.md` to understand context
2. Identify current phase and pending tasks
3. Make incremental progress
4. Update `log.md` with changes
5. Commit and push to git
6. Tag releases at phase completion

---

## Backlog / Known Issues

| Issue | Priority | Notes |
|-------|----------|-------|
| Regina Maria headless CAPTCHA bypass | Low | Site detects headless mode despite extensive stealth. Fallback to visible browser works fine. Revisit when we have more time for advanced evasion techniques. |

---

## Current Status
**Phase:** 2 NEARLY COMPLETE, Phase 4 PARTIAL
**Focus:** Finishing Phase 2, preparing for production

### Phase 0 - COMPLETE ✓
- [x] Synevo crawler works reliably (headless, downloads all docs)
- [x] Regina Maria crawler works (fallback to visible browser for CAPTCHA)
- [x] CAPTCHA handling integrated (auto-detects, opens visible browser)
- [x] Real-time sync status feedback in UI
- [x] Basic document storage and management
- [x] AI parsing works (extracts biomarkers from PDFs)
- [x] Dashboard shows imported documents and stats

### Phase 1 - COMPLETE ✓
- [x] Biomarkers page: Table view with all extracted biomarkers
- [x] Search/filter biomarkers by name, status (All/Issues)
- [x] Evolution page: Historical chart for each biomarker (Recharts)
- [x] Flag HIGH/LOW values visually (color-coded badges)
- [x] Dashboard: Real recent biomarkers + alerts count
- [x] API endpoints: /recent-biomarkers, /alerts-count, /evolution/{name}
- [x] Biomarkers grouped by category, collapsible sections
- [x] Sort biomarkers by issues first or most recent
- [x] PDF view icons to see source documents

### Phase 2 - NEARLY COMPLETE (98%)
- [x] User registration and authentication (email/password)
- [x] Google OAuth authentication
- [x] Secure credential storage (Fernet encryption)
- [x] AI Generalist Agent: Reviews health history, identifies concerns
- [x] AI Specialist Agents: Cardiology, Endocrinology, Hematology, Hepatology, Nephrology
- [x] Health Report generation with findings and recommendations
- [x] Health Reports page in frontend with detailed progress UI
- [x] Document deletion with cascade delete of biomarkers
- [x] Edit linked account credentials
- [x] Full localization (Romanian/English) for all pages
- [x] Email verification for registration (AWS SES configured and working)
- [ ] Report history and comparison

### Phase 4 - PARTIAL (Production Deployment)
- [x] PostgreSQL database (production) - Running on Contabo
- [x] Cloud deployment - Contabo VPS (62.171.163.23)
- [x] Nginx reverse proxy configured
- [x] Systemd services for API and Xvfb
- [x] SSL/HTTPS via Let's Encrypt
- [x] Custom domain: analize.online
- [ ] GDPR compliance
- [ ] Backup and disaster recovery
- [ ] Monitoring and alerting

### Deployment Info
- **Domain:** https://analize.online (SSL via Let's Encrypt, expires 2026-04-24)
- **Server:** Contabo VPS 62.171.163.23
- **Frontend:** https://analize.online (Nginx serving static files)
- **Backend:** https://analize.online/api (FastAPI via Uvicorn, port 8000 internal)
- **Database:** PostgreSQL (local on server)
- **Email:** AWS SES (eu-central-1)
- **Git:** Auto-deploy via `git pull` + rebuild

### AWS SES Credentials (NEVER FORGET)
```
SMTP_HOST=email-smtp.eu-central-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=AKIA2FDNCNUTSNZZEMUJ
SMTP_PASS=nCKQN5gaKGI2JriUFB2IL4G4S5ioh9obg1r1dP1mBDY=
SMTP_FROM=noreply@analize.online
AWS_REGION=eu-central-1
```
These credentials are configured in `/opt/healthy/.env` on the production server.

**IMPORTANT - Environment Differences:**
- **Local development:** Windows (use Windows paths like `c:\OldD\_Projects\Healthy`)
- **Production server:** Linux (use Linux paths like `/opt/healthy`)
- When running bash commands locally, be aware of Windows vs Linux syntax differences
- SSH to server for deployment: `ssh root@62.171.163.23`

### Next Steps
1. ~~Get domain name~~ DONE: analize.online
2. ~~Set up SSL/HTTPS with Let's Encrypt~~ DONE
3. ~~Configure AWS SES credentials~~ DONE (in .env)
4. ~~Complete localization~~ DONE (all pages translated)
5. ~~Implement email verification for registration~~ DONE
6. Implement report comparison feature
7. Implement per-user encryption (see `PER_USER_ENCRYPTION_PLAN.md`)

See **BACKLOG.md** for full list of planned features and technical debt.
