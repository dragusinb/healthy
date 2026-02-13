# Support Tickets Processing Skill

Process user feedback tickets and fix reported issues.

## Workflow

1. **List pending tickets** (run on production server)
   ```bash
   ssh root@62.171.163.23 "cd /opt/healthy && /opt/healthy/backend_v2/venv/bin/python backend_v2/scripts/tickets.py list --status=pending"
   ```

2. **For each pending ticket, show details**
   ```bash
   ssh root@62.171.163.23 "cd /opt/healthy && /opt/healthy/backend_v2/venv/bin/python backend_v2/scripts/tickets.py show <id>"
   ```

3. **View screenshot if available**
   - Screenshots are stored on production at: `/opt/healthy/data/uploads/support/<ticket_id>/screenshot.png`
   - Copy to local and view: `scp root@62.171.163.23:/opt/healthy/data/uploads/support/<ticket_id>/screenshot.png /tmp/`
   - Use the Read tool to view: `/tmp/screenshot.png`

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

6. **Resolve the ticket** (after deploying the fix)
   ```bash
   ssh root@62.171.163.23 "cd /opt/healthy && /opt/healthy/backend_v2/venv/bin/python backend_v2/scripts/tickets.py resolve <id> 'Description of what was fixed'"
   ```

## Commands Reference

All commands run on the production server via SSH:

```bash
# Shorthand for running ticket commands
TICKETS="ssh root@62.171.163.23 'cd /opt/healthy && /opt/healthy/backend_v2/venv/bin/python backend_v2/scripts/tickets.py'"

# List all pending tickets
$TICKETS list --status=pending

# Show ticket details
$TICKETS show <id>

# Mark as fixed (sends email notification to user)
$TICKETS resolve <id> "Fixed by updating..."

# Skip if not actionable
$TICKETS skip <id> "Not a bug, user error"

# Escalate if needs human
$TICKETS escalate <id> "Requires database change"

# View statistics
$TICKETS stats
```

## Guidelines

- Always read the ticket description and view the screenshot
- Look at the page URL to identify which component is affected
- Make minimal, focused fixes
- Include a clear description of what was fixed in the resolve message
- If the issue is unclear or requires major changes, escalate it
- If it's not a valid bug, skip it with an explanation
