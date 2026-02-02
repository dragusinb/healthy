#!/bin/bash
# Post-deployment bug detection check
#
# Run this script after deploying to catch regressions immediately.
# It will run consistency tests against the live API and report any failures.
#
# Usage:
#   ./post_deploy_check.sh
#
# Exit codes:
#   0 - All checks passed
#   1 - Some checks failed (review BUGS.md)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================"
echo "Post-Deployment Bug Detection Check"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo ""

# Check if we're on the server
if [ -f /opt/healthy/venv/bin/python ]; then
    PYTHON="/opt/healthy/venv/bin/python"
    cd /opt/healthy
else
    PYTHON="${PYTHON:-python}"
    cd "$PROJECT_ROOT"
fi

# Wait for API to be ready
echo "Waiting for API to be ready..."
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8000/admin/vault/status > /dev/null 2>&1; then
        echo "API is ready."
        break
    fi
    sleep 1
    WAITED=$((WAITED + 1))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "ERROR: API did not become ready within ${MAX_WAIT} seconds"
    exit 1
fi

# Check vault status
echo ""
echo "Checking vault status..."
VAULT_STATUS=$(curl -s http://localhost:8000/admin/vault/status)
IS_UNLOCKED=$(echo "$VAULT_STATUS" | grep -o '"is_unlocked":[^,}]*' | cut -d':' -f2)

if [ "$IS_UNLOCKED" != "true" ]; then
    echo "WARNING: Vault is locked! Some tests will be skipped."
    echo "Please unlock the vault before running full bug detection."
fi

# Run bug detection
echo ""
echo "Running bug detection tests..."
echo ""

$PYTHON -m backend_v2.scripts.run_bug_detection \
    --target live \
    --report-bugs \
    --post-deploy

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "============================================"
    echo " POST-DEPLOYMENT CHECK PASSED"
    echo "============================================"
else
    echo "============================================"
    echo " POST-DEPLOYMENT CHECK FAILED"
    echo " Review BUGS.md for detected issues"
    echo "============================================"
fi

exit $EXIT_CODE
