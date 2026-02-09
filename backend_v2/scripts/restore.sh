#!/bin/bash
# Healthy Database Restore Script
# Restores a PostgreSQL database from a backup file
#
# Usage: ./restore.sh <backup_file> [--dry-run]
#   backup_file: Path to the backup file (.sql.gz or .sql.gz.gpg)
#   --dry-run: Show what would be done without executing
#
# WARNING: This will DROP and RECREATE the database!

set -e

# Configuration
DB_NAME="${DB_NAME:-healthy}"
GPG_PASSPHRASE_FILE="${GPG_PASSPHRASE_FILE:-}"  # Path to file containing GPG passphrase

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
BACKUP_FILE=""
DRY_RUN=false

for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
        *) BACKUP_FILE="$arg" ;;
    esac
done

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not specified${NC}"
    echo "Usage: $0 <backup_file> [--dry-run]"
    echo ""
    echo "Examples:"
    echo "  $0 /opt/healthy/backups/healthy_20250209_030000.sql.gz"
    echo "  $0 /opt/healthy/backups/healthy_20250209_030000.sql.gz.gpg --dry-run"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Determine file type and prepare for restoration
TEMP_DIR=$(mktemp -d)
RESTORE_FILE=""

if [[ "$BACKUP_FILE" == *.gpg ]]; then
    log "Detected encrypted backup file"
    DECRYPTED_FILE="${TEMP_DIR}/$(basename "${BACKUP_FILE%.gpg}")"

    if [ "$DRY_RUN" = true ]; then
        log "[DRY RUN] Would decrypt $BACKUP_FILE to $DECRYPTED_FILE"
        RESTORE_FILE="$DECRYPTED_FILE"
    else
        log "Decrypting backup file..."
        if [ -n "$GPG_PASSPHRASE_FILE" ] && [ -f "$GPG_PASSPHRASE_FILE" ]; then
            gpg --batch --passphrase-file "$GPG_PASSPHRASE_FILE" --decrypt --output "$DECRYPTED_FILE" "$BACKUP_FILE"
        else
            gpg --decrypt --output "$DECRYPTED_FILE" "$BACKUP_FILE"
        fi
        RESTORE_FILE="$DECRYPTED_FILE"
    fi
elif [[ "$BACKUP_FILE" == *.sql.gz ]]; then
    RESTORE_FILE="$BACKUP_FILE"
else
    error "Unsupported backup format. Expected .sql.gz or .sql.gz.gpg"
fi

# Display backup info
log "Backup file: $BACKUP_FILE"
log "Database: $DB_NAME"
log "File size: $(du -h "$BACKUP_FILE" | cut -f1)"

if [ "$DRY_RUN" = true ]; then
    echo ""
    log "[DRY RUN] Would perform the following actions:"
    log "  1. Stop healthy-api service"
    log "  2. Terminate all database connections"
    log "  3. Drop database: $DB_NAME"
    log "  4. Create database: $DB_NAME"
    log "  5. Restore from: $RESTORE_FILE"
    log "  6. Start healthy-api service"
    log "  7. Unlock vault (requires master password)"
    echo ""
    log "[DRY RUN] No changes were made"
    rm -rf "$TEMP_DIR"
    exit 0
fi

# Confirm before proceeding
echo ""
echo -e "${RED}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║                        WARNING                           ║${NC}"
echo -e "${RED}║  This will DROP and RECREATE the database!               ║${NC}"
echo -e "${RED}║  All existing data will be replaced with the backup.     ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
read -p "Type 'RESTORE' to confirm: " CONFIRM

if [ "$CONFIRM" != "RESTORE" ]; then
    log "Restore cancelled"
    rm -rf "$TEMP_DIR"
    exit 0
fi

# Stop the API service
log "Stopping healthy-api service..."
systemctl stop healthy-api 2>/dev/null || warn "Could not stop healthy-api (may not be running)"

# Wait for connections to close
sleep 2

# Terminate all connections to the database
log "Terminating database connections..."
psql -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" 2>/dev/null || true

# Drop and recreate database
log "Dropping database..."
dropdb "$DB_NAME" 2>/dev/null || warn "Database may not exist"

log "Creating database..."
createdb "$DB_NAME"

# Restore the backup
log "Restoring database from backup..."
if [[ "$RESTORE_FILE" == *.gz ]]; then
    gunzip -c "$RESTORE_FILE" | psql -d "$DB_NAME" -q
else
    psql -d "$DB_NAME" -q -f "$RESTORE_FILE"
fi

log "Database restored successfully"

# Cleanup temp files
rm -rf "$TEMP_DIR"

# Start the API service
log "Starting healthy-api service..."
systemctl start healthy-api 2>/dev/null || warn "Could not start healthy-api"

# Wait for service to start
sleep 3

# Check if service is running
if systemctl is-active --quiet healthy-api 2>/dev/null; then
    log "healthy-api service is running"
else
    warn "healthy-api service may not be running - check manually"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Restore completed successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo "  1. Unlock the vault: curl -X POST https://analize.online/api/admin/vault/unlock -H 'Content-Type: application/json' -d '{\"master_password\": \"YOUR_PASSWORD\"}'"
echo "  2. Verify application: curl https://analize.online/api/health"
echo "  3. Test login and functionality"
echo ""

exit 0
