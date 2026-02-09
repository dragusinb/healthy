#!/bin/bash
# Healthy Monitoring Script
# Checks system health and sends alerts if issues are detected
#
# Usage: ./monitor.sh [--alert-only]
#   --alert-only: Only output if there are alerts (for cron)
#
# Cron example (every 5 minutes):
#   */5 * * * * /opt/healthy/backend_v2/scripts/monitor.sh --alert-only 2>&1 | mail -E -s "[ALERT] Healthy System Alert" admin@example.com

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
NOTIFY_EMAIL="${NOTIFY_EMAIL:-}"
DISK_WARN_THRESHOLD=80
DISK_CRIT_THRESHOLD=90
MEM_WARN_THRESHOLD=80
MEM_CRIT_THRESHOLD=90
CPU_WARN_THRESHOLD=80

# Parse arguments
ALERT_ONLY=false
for arg in "$@"; do
    case $arg in
        --alert-only) ALERT_ONLY=true ;;
    esac
done

ALERTS=""
WARNINGS=""

# Check API health endpoint
check_api() {
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/health" --max-time 10 2>/dev/null || echo "000")
    if [ "$RESPONSE" != "200" ]; then
        ALERTS="${ALERTS}CRITICAL: API health check failed (HTTP $RESPONSE)\n"
        return 1
    fi

    # Parse health response
    HEALTH=$(curl -s "${API_URL}/health" --max-time 10 2>/dev/null || echo '{"status":"error"}')
    STATUS=$(echo "$HEALTH" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

    if [ "$STATUS" = "unhealthy" ]; then
        ALERTS="${ALERTS}CRITICAL: System status is unhealthy\n"
        ALERTS="${ALERTS}$(echo "$HEALTH" | grep -o '"issues":\[[^]]*\]')\n"
    elif [ "$STATUS" = "degraded" ]; then
        WARNINGS="${WARNINGS}WARNING: System status is degraded\n"
        WARNINGS="${WARNINGS}$(echo "$HEALTH" | grep -o '"issues":\[[^]]*\]')\n"
    fi
}

# Check disk space
check_disk() {
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
    if [ "$DISK_USAGE" -ge "$DISK_CRIT_THRESHOLD" ]; then
        ALERTS="${ALERTS}CRITICAL: Disk usage at ${DISK_USAGE}%\n"
    elif [ "$DISK_USAGE" -ge "$DISK_WARN_THRESHOLD" ]; then
        WARNINGS="${WARNINGS}WARNING: Disk usage at ${DISK_USAGE}%\n"
    fi
}

# Check memory
check_memory() {
    MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
    if [ "$MEM_USAGE" -ge "$MEM_CRIT_THRESHOLD" ]; then
        ALERTS="${ALERTS}CRITICAL: Memory usage at ${MEM_USAGE}%\n"
    elif [ "$MEM_USAGE" -ge "$MEM_WARN_THRESHOLD" ]; then
        WARNINGS="${WARNINGS}WARNING: Memory usage at ${MEM_USAGE}%\n"
    fi
}

# Check CPU (5-minute load average)
check_cpu() {
    CPU_CORES=$(nproc)
    LOAD_AVG=$(cat /proc/loadavg | awk '{print $2}')
    # Convert load average to percentage of total capacity
    CPU_USAGE=$(echo "$LOAD_AVG $CPU_CORES" | awk '{print int($1/$2 * 100)}')
    if [ "$CPU_USAGE" -ge "$CPU_WARN_THRESHOLD" ]; then
        WARNINGS="${WARNINGS}WARNING: CPU load at ${CPU_USAGE}% (load: ${LOAD_AVG})\n"
    fi
}

# Check if healthy-api service is running
check_service() {
    if ! systemctl is-active --quiet healthy-api 2>/dev/null; then
        ALERTS="${ALERTS}CRITICAL: healthy-api service is not running\n"
    fi
}

# Check recent sync failures
check_syncs() {
    # Check via API if available
    SYNC_CHECK=$(curl -s "${API_URL}/admin/scheduler-status" -H "Authorization: Bearer ${ADMIN_TOKEN:-}" --max-time 5 2>/dev/null || echo "")
    if [ -n "$SYNC_CHECK" ]; then
        FAILED=$(echo "$SYNC_CHECK" | grep -o '"failed_syncs_24h":[0-9]*' | cut -d':' -f2 || echo "0")
        if [ "$FAILED" -gt 10 ]; then
            WARNINGS="${WARNINGS}WARNING: ${FAILED} failed syncs in last 24 hours\n"
        fi
    fi
}

# Check backup status
check_backup() {
    BACKUP_DIR="${BACKUP_DIR:-/opt/healthy/backups}"
    if [ -d "$BACKUP_DIR" ]; then
        LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/healthy_*.sql.gz* 2>/dev/null | head -1)
        if [ -z "$LATEST_BACKUP" ]; then
            WARNINGS="${WARNINGS}WARNING: No backups found in $BACKUP_DIR\n"
        else
            # Check if backup is older than 25 hours (should be daily)
            BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 3600 ))
            if [ "$BACKUP_AGE" -gt 25 ]; then
                WARNINGS="${WARNINGS}WARNING: Latest backup is ${BACKUP_AGE} hours old\n"
            fi
        fi
    fi
}

# Run all checks
check_api
check_disk
check_memory
check_cpu
check_service
check_syncs
check_backup

# Output results
if [ -n "$ALERTS" ] || [ -n "$WARNINGS" ]; then
    echo "=== Healthy System Monitor ==="
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Server: $(hostname)"
    echo ""

    if [ -n "$ALERTS" ]; then
        echo "=== ALERTS ==="
        echo -e "$ALERTS"
    fi

    if [ -n "$WARNINGS" ]; then
        echo "=== WARNINGS ==="
        echo -e "$WARNINGS"
    fi

    # Send email notification if configured
    if [ -n "$NOTIFY_EMAIL" ] && [ -n "$ALERTS" ]; then
        (
            echo "Healthy System Monitor Alert"
            echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
            echo "Server: $(hostname)"
            echo ""
            echo "=== ALERTS ==="
            echo -e "$ALERTS"
            if [ -n "$WARNINGS" ]; then
                echo "=== WARNINGS ==="
                echo -e "$WARNINGS"
            fi
        ) | mail -s "[ALERT] Healthy System Issues Detected" "$NOTIFY_EMAIL"
    fi

    exit 1
elif [ "$ALERT_ONLY" = false ]; then
    echo "=== Healthy System Monitor ==="
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Status: All checks passed"
    echo ""
    echo "API: OK"
    echo "Disk: $(df / | tail -1 | awk '{print $5}')"
    echo "Memory: $(free | grep Mem | awk '{print int($3/$2 * 100)}')%"
    echo "Service: $(systemctl is-active healthy-api 2>/dev/null || echo 'unknown')"
fi

exit 0
