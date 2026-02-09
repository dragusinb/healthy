# Disaster Recovery Runbook

This document outlines procedures for backing up, monitoring, and recovering the Healthy (Analize.online) application.

## Quick Reference

| Component | Location | Backup Frequency |
|-----------|----------|------------------|
| PostgreSQL Database | localhost:5432 | Daily at 3 AM |
| Encrypted Documents | /opt/healthy/data/encrypted/ | Daily |
| Application Config | /opt/healthy/.env | Manual (on changes) |
| SSL Certificates | /etc/letsencrypt/ | Auto-renewed |

## Backup System

### Automated Backups

Backups are configured to run daily via cron:

```bash
# /etc/cron.d/healthy-backup
0 3 * * * root /opt/healthy/backend_v2/scripts/backup.sh --notify >> /var/log/healthy-backup.log 2>&1
```

### Backup Script

Location: `/opt/healthy/backend_v2/scripts/backup.sh`

Features:
- PostgreSQL database dump (compressed with gzip)
- Optional GPG encryption
- Optional S3 upload
- Automatic cleanup of old backups (30-day retention)
- Email notifications

**Manual backup:**
```bash
# Local backup only
/opt/healthy/backend_v2/scripts/backup.sh

# With S3 upload
S3_BUCKET=your-bucket /opt/healthy/backend_v2/scripts/backup.sh --upload

# With email notification
NOTIFY_EMAIL=admin@example.com /opt/healthy/backend_v2/scripts/backup.sh --notify
```

### Backup Locations

- **Local:** `/opt/healthy/backups/`
- **Cloud (optional):** `s3://your-bucket/backups/`

### Verifying Backups

```bash
# List local backups
ls -la /opt/healthy/backups/

# Check backup file integrity
gunzip -t /opt/healthy/backups/healthy_YYYYMMDD_HHMMSS.sql.gz

# View backup contents (first 50 lines)
zcat /opt/healthy/backups/healthy_YYYYMMDD_HHMMSS.sql.gz | head -50
```

---

## Monitoring System

### Health Check Endpoint

The `/health` endpoint provides comprehensive system status:

```bash
curl https://analize.online/api/health
```

Response includes:
- Overall status: `healthy`, `degraded`, or `unhealthy`
- Database connectivity
- Disk space usage
- Memory usage
- Vault status

### Monitoring Script

Location: `/opt/healthy/backend_v2/scripts/monitor.sh`

**Manual check:**
```bash
/opt/healthy/backend_v2/scripts/monitor.sh
```

**Cron setup (every 5 minutes):**
```bash
# /etc/cron.d/healthy-monitor
*/5 * * * * root NOTIFY_EMAIL=admin@example.com /opt/healthy/backend_v2/scripts/monitor.sh --alert-only 2>&1
```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Disk Usage | 80% | 90% |
| Memory Usage | 80% | 90% |
| CPU Load | 80% | - |
| Backup Age | - | 25 hours |

---

## Recovery Procedures

### Scenario 1: Database Corruption

**Symptoms:** Application errors, data inconsistency, failed queries

**Recovery:**
```bash
# 1. Stop the application
systemctl stop healthy-api

# 2. List available backups
ls -la /opt/healthy/backups/

# 3. Restore from backup (interactive)
/opt/healthy/backend_v2/scripts/restore.sh /opt/healthy/backups/healthy_YYYYMMDD_HHMMSS.sql.gz

# 4. Unlock the vault
curl -X POST https://analize.online/api/admin/vault/unlock \
  -H "Content-Type: application/json" \
  -d '{"master_password": "YOUR_MASTER_PASSWORD"}'

# 5. Verify health
curl https://analize.online/api/health
```

### Scenario 2: Server Failure (New Server)

**Prerequisites:**
- New server with same OS (Linux)
- PostgreSQL installed
- Python 3.10+ installed
- Nginx installed
- Access to backups (S3 or local copy)

**Recovery Steps:**

```bash
# 1. Clone the repository
cd /opt
git clone https://github.com/dragusinb/healthy.git

# 2. Install dependencies
cd /opt/healthy/backend_v2
pip install -r requirements.txt

# 3. Copy environment file (from secure backup)
cp /path/to/backup/.env /opt/healthy/.env

# 4. Create database
sudo -u postgres createdb healthy

# 5. Download and restore backup
aws s3 cp s3://your-bucket/backups/latest.sql.gz /tmp/
/opt/healthy/backend_v2/scripts/restore.sh /tmp/latest.sql.gz

# 6. Restore encrypted documents
aws s3 cp s3://your-bucket/backups/healthy_data_YYYYMMDD.tar.gz /tmp/
tar -xzf /tmp/healthy_data_YYYYMMDD.tar.gz -C /opt/healthy/data/

# 7. Configure systemd service
cp /opt/healthy/deploy/healthy-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable healthy-api
systemctl start healthy-api

# 8. Configure Nginx
cp /opt/healthy/deploy/nginx.conf /etc/nginx/sites-available/healthy
ln -s /etc/nginx/sites-available/healthy /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 9. Update DNS (if IP changed)
# Point analize.online to new server IP

# 10. Renew SSL certificate
certbot --nginx -d analize.online

# 11. Unlock vault
curl -X POST https://analize.online/api/admin/vault/unlock \
  -H "Content-Type: application/json" \
  -d '{"master_password": "YOUR_MASTER_PASSWORD"}'

# 12. Verify health
curl https://analize.online/api/health
```

### Scenario 3: Vault Password Lost

**WARNING:** If the vault master password is lost, all encrypted data is **permanently inaccessible**.

There is no recovery mechanism for vault passwords. Users must:
1. Create new accounts
2. Re-link medical provider accounts
3. Re-sync documents

**Prevention:**
- Store vault password in secure location (password manager, safe)
- Create multiple copies in secure, separate locations
- Never store in plain text on the server

### Scenario 4: Application Crash / High Load

**Quick Recovery:**
```bash
# Restart the application
systemctl restart healthy-api

# Check logs
journalctl -u healthy-api -n 100 --no-pager

# Check system resources
htop
df -h
free -m
```

**If persistent issues:**
1. Check `/var/log/healthy.log` for errors
2. Check database connections: `psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='healthy';"`
3. Restart Nginx: `systemctl restart nginx`
4. Check SSL: `curl -v https://analize.online/api/health`

---

## Preventive Measures

### Daily Automated Checks

1. **Backup verification** - Check backup file exists and is recent
2. **Health endpoint** - Verify API responds correctly
3. **Disk space** - Ensure adequate free space
4. **SSL certificate** - Check expiration (auto-renewed but verify)

### Weekly Manual Checks

1. Review backup sizes (should be consistent)
2. Check error logs for patterns
3. Verify sync success rates
4. Test restore procedure (on staging/dev)

### Monthly Tasks

1. **Full restore test** on a separate environment
2. Review and update this runbook
3. Audit user access and permissions
4. Update dependencies if needed

---

## Contact Information

| Role | Contact |
|------|---------|
| Primary Admin | [Configure in .env] |
| Hosting Provider | Contabo Support |
| Domain Registrar | [Your registrar] |
| AWS Support | [If using S3] |

---

## Important Files

| File | Purpose |
|------|---------|
| `/opt/healthy/.env` | Application secrets and configuration |
| `/opt/healthy/backups/` | Database backups |
| `/opt/healthy/data/encrypted/` | Encrypted user documents |
| `/var/log/healthy.log` | Application logs |
| `/var/log/healthy-backup.log` | Backup script logs |

---

## Vault Information

The application uses AES-256-GCM encryption via a vault system:

- **Vault Status:** `GET /api/admin/vault/status`
- **Initialize (first time):** `POST /api/admin/vault/initialize`
- **Unlock (after restart):** `POST /api/admin/vault/unlock`
- **Lock:** `POST /api/admin/vault/lock`

**After every server restart, the vault must be unlocked manually.**

---

*Last Updated: 2026-02-09*
