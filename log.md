# Healthy Project - Development Log

## Session: 2026-02-01

### Localization Completed
All frontend pages are now fully translated with dynamic locale support.

**Files Updated:**
- `frontend_v2/src/pages/Admin.jsx` - 40+ hardcoded English strings translated
- `frontend_v2/src/pages/Evolution.jsx` - Dynamic locale for date formatting, translated "Ref:" label
- `frontend_v2/src/pages/HealthReports.jsx` - Analysis steps and UI text translated
- `frontend_v2/src/locales/ro.json` - Added admin, evolution, and healthReports translation keys
- `frontend_v2/src/locales/en.json` - Matching English translations

**Key Changes:**
- Date formatting now uses user's language setting (ro-RO or en-US)
- All UI text uses `t()` translation function from i18next
- Child components receive `t` prop when needed

### Per-User Encryption Plan Created
Created `PER_USER_ENCRYPTION_PLAN.md` with comprehensive implementation guide:
- Two-level key hierarchy (Password → PDK → Vault Key → Data)
- AES-256-GCM encryption with PBKDF2 key derivation
- Database schema changes for encrypted columns
- Session management with Redis for vault keys
- Gradual migration strategy (encrypt on login)
- Document file encryption
- 6-week implementation timeline

### Domain Ready
Domain `analize.online` is available. Next steps:
1. Configure DNS A record → 62.171.163.23
2. Set up Nginx server block for domain
3. Install SSL with Let's Encrypt (certbot)

### Commits
- `0e1b322` - Complete localization for Admin and Evolution pages, add encryption plan
- `ba289a6` - Add Romanian translations to HealthReports and fix hardcoded text
- `7529628` - Fix syntax error in health_agents.py
- `8af285f` - Fix placeholder text in gap analysis and hardcoded specialists
- `85b0241` - Include qualitative test results in AI parser
- `43687c6` - Fix document import to use file_hash for deduplication

---

## Session: 2026-01-20

### Project Overview
**Healthy** is a medical document aggregation platform that:
1. Crawls medical lab providers (Regina Maria, Synevo) to download PDF results
2. Parses PDFs using OpenAI GPT-4o to extract biomarkers
3. Stores biomarker data (test name, value, unit, reference range, flags)
4. Displays data in a React web interface with trend charts

**Tech Stack:**
- Backend: FastAPI + SQLAlchemy + SQLite (`backend_v2/`)
- Frontend: React 19 + Vite + Tailwind CSS (`frontend_v2/`)
- Crawlers: Playwright (async browser automation)
- AI: OpenAI GPT-4o for PDF parsing

**URLs:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Default Login:**
- Email: `dragusinb@gmail.com`
- Password: `J@guar123`

---

### Issues Fixed

#### 1. Synevo Crawler - Download Timeout
**Problem:** Downloads were timing out because Synevo changed how PDFs are served (no longer triggers browser download event).

**Fix:** (`backend_v2/services/synevo_crawler.py`)
- Implemented 3 fallback download methods:
  1. Browser download event (original method)
  2. Direct HTTP request with session cookies (using `aiohttp`)
  3. Open PDF URL in new tab and capture response body

#### 2. Regina Maria Crawler - Cookie Consent Overlay
**Problem:** OneTrust cookie consent dialog creates overlay blocking all clicks.

**Fix:** (`backend_v2/services/regina_maria_crawler.py`)
- Added `_dismiss_cookie_consent()` method with 3 approaches:
  1. Click accept button by text
  2. Click by OneTrust ID (`#onetrust-accept-btn-handler`)
  3. JavaScript removal of overlay elements

#### 3. Regina Maria Crawler - Page Structure Changed
**Problem:** No "Descarca" (Download) buttons on main Analize page anymore.

**Fix:**
- Added fallback strategy to navigate to detail pages ("Vezi detalii raport" buttons)
- Look for download buttons on detail pages
- Navigate back and continue to next document

#### 4. Regina Maria Crawler - reCAPTCHA
**Problem:** reCAPTCHA blocks automated logins.

**Fix:**
- Changed default to `headless=False` (browser window visible)
- Extended wait time to 3 minutes for manual solving
- User can solve reCAPTCHA manually in the browser window

#### 5. Windows Asyncio Subprocess Error
**Problem:** Python 3.14 on Windows throws `NotImplementedError` when Playwright tries to spawn subprocess.

**Fix:** (`backend_v2/main.py`)
```python
import sys
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

---

### Files Modified
- `backend_v2/services/synevo_crawler.py` - Multi-method PDF download
- `backend_v2/services/regina_maria_crawler.py` - Cookie consent, detail pages, reCAPTCHA handling
- `backend_v2/services/crawlers_manager.py` - Added `headless` parameter
- `backend_v2/requirements.txt` - Added `playwright`, `aiohttp`, `pypdf`
- `backend_v2/main.py` - Windows asyncio fix
- `backend_v2/test_crawlers.py` - NEW: Manual test script for crawlers

---

### How to Start Servers
```bash
# From project root (C:\OldD\_Projects\Healthy)

# Backend
python -m uvicorn backend_v2.main:app --reload --port 8000

# Frontend
cd frontend_v2 && npm run dev
```

---

### How to Test Crawlers Manually
```bash
# Install Playwright browser
python -m playwright install chromium

# Test Synevo (CNP = Romanian ID number)
python -m backend_v2.test_crawlers -p synevo -u YOUR_CNP -pw YOUR_PASSWORD

# Test Regina Maria (browser opens for manual reCAPTCHA)
python -m backend_v2.test_crawlers -p regina -u YOUR_EMAIL -pw YOUR_PASSWORD
```

---

#### 6. Windows Asyncio Subprocess Fix (Final Solution)
**Problem:** The asyncio event loop policy fix in main.py didn't work because uvicorn creates its own event loop.

**Fix:** Changed crawlers from async to sync Playwright:
- `backend_v2/services/base.py` - Now uses `sync_playwright` and `ThreadPoolExecutor`
- `backend_v2/services/synevo_crawler.py` - Converted to sync methods (`login_sync`, `navigate_to_records_sync`, `extract_documents_sync`)
- `backend_v2/services/regina_maria_crawler.py` - Converted to sync methods
- The `run()` method now runs sync code in a thread pool via `run_in_executor()`

---

### Pending Issues
- [ ] Test crawlers with real credentials
- [ ] Regina Maria may still need selector updates if site changed further
- [ ] Password encryption for LinkedAccount (currently stored plaintext)

---

### Git Repository
- **URL:** https://github.com/dragusinb/healthy.git
- **Tag:** `v0.0-foundation` - Initial project setup

---

### Next Steps (Phase 0 Completion)
1. Test Synevo crawler with real credentials
2. Test Regina Maria crawler with real credentials (solve CAPTCHA manually)
3. Verify documents are downloaded and stored
4. Once crawlers work reliably, tag `v0.1-mvp`
