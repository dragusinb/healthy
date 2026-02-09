#!/bin/bash
# Healthy Backup Script
# Creates encrypted PostgreSQL backups and uploads to cloud storage
#
# Usage: ./backup.sh [--upload] [--notify]
#   --upload: Upload to S3 (requires AWS CLI configured)
#   --notify: Send email notification on completion/failure
#
# Cron example (daily at 3 AM):
#   0 3 * * * /opt/healthy/backend_v2/scripts/backup.sh --notify >> /var/log/healthy-backup.log 2>&1

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/opt/healthy/backups}"
DB_NAME="${DB_NAME:-healthy}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-}"
NOTIFY_EMAIL="${NOTIFY_EMAIL:-}"
GPG_RECIPIENT="${GPG_RECIPIENT:-}"  # GPG key ID for encryption

# Timestamp for backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="healthy_${TIMESTAMP}.sql.gz"
ENCRYPTED_FILE="${BACKUP_FILE}.gpg"

# Parse arguments
UPLOAD=false
NOTIFY=false
for arg in "$@"; do
    case $arg in
        --upload) UPLOAD=true ;;
        --notify) NOTIFY=true ;;
    esac
done

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Error handler
error_exit() {
    log "ERROR: $1"
    if [ "$NOTIFY" = true ] && [ -n "$NOTIFY_EMAIL" ]; then
        echo "Backup failed: $1" | mail -s "[ALERT] Healthy Backup Failed" "$NOTIFY_EMAIL"
    fi
    exit 1
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log "Starting backup of database: $DB_NAME"

# Create PostgreSQL dump
log "Creating database dump..."
pg_dump "$DB_NAME" | gzip > "$BACKUP_DIR/$BACKUP_FILE" || error_exit "Database dump failed"

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
log "Backup created: $BACKUP_FILE (${BACKUP_SIZE})"

# Encrypt backup if GPG recipient is configured
if [ -n "$GPG_RECIPIENT" ]; then
    log "Encrypting backup with GPG..."
    gpg --encrypt --recipient "$GPG_RECIPIENT" --output "$BACKUP_DIR/$ENCRYPTED_FILE" "$BACKUP_DIR/$BACKUP_FILE" || error_exit "Encryption failed"
    rm "$BACKUP_DIR/$BACKUP_FILE"
    BACKUP_FILE="$ENCRYPTED_FILE"
    log "Backup encrypted: $ENCRYPTED_FILE"
fi

# Upload to S3 if configured and --upload flag is set
if [ "$UPLOAD" = true ] && [ -n "$S3_BUCKET" ]; then
    log "Uploading to S3: s3://${S3_BUCKET}/backups/"
    aws s3 cp "$BACKUP_DIR/$BACKUP_FILE" "s3://${S3_BUCKET}/backups/$BACKUP_FILE" || error_exit "S3 upload failed"
    log "Upload complete"
fi

# Cleanup old backups (local)
log "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -name "healthy_*.sql.gz*" -mtime +$RETENTION_DAYS -delete
REMAINING=$(ls -1 "$BACKUP_DIR"/healthy_*.sql.gz* 2>/dev/null | wc -l)
log "Remaining local backups: $REMAINING"

# Cleanup old backups (S3)
if [ "$UPLOAD" = true ] && [ -n "$S3_BUCKET" ]; then
    log "Cleaning up S3 backups older than ${RETENTION_DAYS} days..."
    CUTOFF_DATE=$(date -d "-${RETENTION_DAYS} days" +%Y-%m-%d)
    aws s3 ls "s3://${S3_BUCKET}/backups/" | while read -r line; do
        FILE_DATE=$(echo "$line" | awk '{print $1}')
        FILE_NAME=$(echo "$line" | awk '{print $4}')
        if [[ "$FILE_DATE" < "$CUTOFF_DATE" ]] && [[ "$FILE_NAME" == healthy_* ]]; then
            aws s3 rm "s3://${S3_BUCKET}/backups/$FILE_NAME"
            log "Deleted old S3 backup: $FILE_NAME"
        fi
    done
fi

# Backup data files (encrypted documents)
DATA_DIR="/opt/healthy/data/encrypted"
if [ -d "$DATA_DIR" ]; then
    log "Backing up encrypted documents..."
    DATA_BACKUP="healthy_data_${TIMESTAMP}.tar.gz"
    tar -czf "$BACKUP_DIR/$DATA_BACKUP" -C /opt/healthy/data encrypted || log "WARNING: Data backup failed (non-critical)"

    if [ -f "$BACKUP_DIR/$DATA_BACKUP" ]; then
        DATA_SIZE=$(du -h "$BACKUP_DIR/$DATA_BACKUP" | cut -f1)
        log "Data backup created: $DATA_BACKUP (${DATA_SIZE})"

        if [ "$UPLOAD" = true ] && [ -n "$S3_BUCKET" ]; then
            aws s3 cp "$BACKUP_DIR/$DATA_BACKUP" "s3://${S3_BUCKET}/backups/$DATA_BACKUP" || log "WARNING: Data S3 upload failed"
        fi
    fi
fi

log "Backup completed successfully"

# Send success notification
if [ "$NOTIFY" = true ] && [ -n "$NOTIFY_EMAIL" ]; then
    echo "Backup completed successfully.

Database: $DB_NAME
Backup: $BACKUP_FILE
Size: $BACKUP_SIZE
Location: $BACKUP_DIR
S3 Upload: $UPLOAD

Remaining local backups: $REMAINING
" | mail -s "[OK] Healthy Backup Complete" "$NOTIFY_EMAIL"
fi

exit 0
