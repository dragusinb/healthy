# Support Tickets Processing Skill

Process user feedback tickets and fix reported issues.

## Workflow

1. **List pending tickets**
   ```bash
   cd /opt/healthy && python backend_v2/scripts/tickets.py list --status=pending
   ```

2. **For each pending ticket, show details**
   ```bash
   python backend_v2/scripts/tickets.py show <id>
   ```

3. **View screenshot if available**
   - Screenshots are stored at: `data/uploads/support/<ticket_id>/screenshot.png`
   - Use the Read tool to view the screenshot image

4. **Map page_url to source files**
   - `/` → `frontend_v2/src/pages/Dashboard.jsx`
   - `/documents` → `frontend_v2/src/pages/Documents.jsx`
   - `/biomarkers` → `frontend_v2/src/pages/Biomarkers.jsx`
   - `/health` → `frontend_v2/src/pages/Health.jsx`
   - `/screenings` → `frontend_v2/src/pages/Screenings.jsx`
   - `/profile` → `frontend_v2/src/pages/Profile.jsx`
   - `/linked-accounts` → `frontend_v2/src/pages/LinkedAccounts.jsx`
   - `/settings` → `frontend_v2/src/pages/NotificationSettings.jsx`
   - `/billing` → `frontend_v2/src/pages/Billing.jsx`
   - `/evolution/*` → `frontend_v2/src/pages/Evolution.jsx`
   - `/admin` → `frontend_v2/src/pages/Admin.jsx`
   - Backend issues → `backend_v2/routers/*.py`

5. **Analyze and fix the issue**
   - Read the relevant source files
   - Understand the reported issue from description + screenshot
   - Make the fix using Edit tool
   - Test locally if possible

6. **Resolve the ticket**
   ```bash
   python backend_v2/scripts/tickets.py resolve <id> "Description of what was fixed"
   ```

## Commands Reference

```bash
# List all pending tickets
python backend_v2/scripts/tickets.py list --status=pending

# Show ticket details
python backend_v2/scripts/tickets.py show <id>

# Mark as fixed
python backend_v2/scripts/tickets.py resolve <id> "Fixed by updating..."

# Skip if not actionable
python backend_v2/scripts/tickets.py skip <id> "Not a bug, user error"

# Escalate if needs human
python backend_v2/scripts/tickets.py escalate <id> "Requires database change"

# View statistics
python backend_v2/scripts/tickets.py stats
```

## Guidelines

- Always read the ticket description and view the screenshot
- Look at the page URL to identify which component is affected
- Make minimal, focused fixes
- Include a clear description of what was fixed in the resolve message
- If the issue is unclear or requires major changes, escalate it
- If it's not a valid bug, skip it with an explanation
