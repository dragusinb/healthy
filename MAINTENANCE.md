# Healthy - Maintenance Guide

**Version:** 1.0
**Last Updated:** 2026-02-10

---

## Quick Reference

| Service | URL | Notes |
|---------|-----|-------|
| Production Site | https://analize.online | Main application |
| API | https://analize.online/api | FastAPI backend |
| API Docs | https://analize.online/api/docs | Swagger UI |
| Health Check | https://analize.online/api/health | System status |
| Grafana | https://analize.online/grafana/ | Monitoring |
| Server | 62.171.163.23 | Contabo VPS |

---

## 1. Server Access

### SSH Access
```bash
ssh root@62.171.163.23
```

### Application Directory
```bash
cd /opt/healthy
```

### Environment Variables
```bash
cat /opt/healthy/.env
```

---

## 2. Service Management

### Check Service Status
```bash
systemctl status healthy-api
systemctl status postgresql
systemctl status nginx
systemctl status prometheus
systemctl status grafana-server
```

### Restart Services
```bash
# Restart API (most common)
systemctl restart healthy-api

# Restart all services
systemctl restart healthy-api nginx postgresql
```

### View Logs
```bash
# API logs (live)
journalctl -u healthy-api -f

# Last 100 lines
journalctl -u healthy-api -n 100

# Nginx access logs
tail -f /var/log/nginx/access.log

# Nginx error logs
tail -f /var/log/nginx/error.log
```

---

## 3. Vault Management (CRITICAL)

### After Every Server Restart
The vault MUST be unlocked after every restart:

```bash
curl -X POST https://analize.online/api/admin/vault/unlock \
  -H "Content-Type: application/json" \
  -d '{"master_password": "YOUR_MASTER_PASSWORD"}'
```

### Check Vault Status
```bash
curl https://analize.online/api/admin/vault/status
```

### Lock Vault (if needed)
```bash
curl -X POST https://analize.online/api/admin/vault/lock \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## 4. Database Operations

### Connect to Database
```bash
PGPASSWORD=HealthyDB123 psql -h localhost -U healthy -d healthy
```

### Quick Stats
```sql
SELECT 'Users' as type, COUNT(*) FROM users
UNION ALL
SELECT 'Documents', COUNT(*) FROM documents
UNION ALL
SELECT 'Biomarkers', COUNT(*) FROM test_results
UNION ALL
SELECT 'Reports', COUNT(*) FROM health_reports;
```

### Database Backup (Manual)
```bash
cd /opt/healthy
pg_dump -U healthy -h localhost healthy > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Automated Backups
- Location: `/opt/healthy/backups/`
- Schedule: Daily at 3 AM
- Retention: 7 days

---

## 5. Deployment

### Pull Latest Code
```bash
cd /opt/healthy
git pull origin main
```

### Install Dependencies
```bash
cd /opt/healthy
source venv/bin/activate
pip install -r backend_v2/requirements.txt
```

### Rebuild Frontend
```bash
cd /opt/healthy/frontend_v2
npm install
npm run build
```

### Restart After Deployment
```bash
systemctl restart healthy-api
# THEN unlock vault!
curl -X POST https://analize.online/api/admin/vault/unlock \
  -H "Content-Type: application/json" \
  -d '{"master_password": "YOUR_MASTER_PASSWORD"}'
```

---

## 6. Monitoring

### Grafana Dashboards
- URL: https://analize.online/grafana/
- Username: admin
- Password: HealthyMonitor2024!

**Available Dashboards:**
1. **System Resources** - CPU, memory, disk
2. **API Performance** - Request rate, response times
3. **Database Health** - Connections, operations

### Alert Rules
- High CPU (>80% for 5 min)
- High Memory (>80% for 5 min)
- High Disk (>80%)
- API Response Time >5s
- API Error Rate >5%
- Database Connections >80

### Manual Health Check
```bash
curl https://analize.online/api/health | jq
```

---

## 7. Common Issues & Solutions

### Issue: "Vault is locked" errors
**Solution:** Unlock the vault (see Section 3)

### Issue: API not responding
**Solution:**
```bash
systemctl status healthy-api
systemctl restart healthy-api
journalctl -u healthy-api -n 50
```

### Issue: High memory usage
**Solution:**
```bash
# Check memory
free -h

# Restart API to free memory
systemctl restart healthy-api
```

### Issue: Disk space full
**Solution:**
```bash
# Check disk usage
df -h

# Clean old backups
cd /opt/healthy/backups
ls -la
rm healthy_backup_OLD*.sql

# Clean old logs
journalctl --vacuum-time=7d
```

### Issue: SSL certificate expired
**Solution:**
```bash
certbot renew
systemctl reload nginx
```

### Issue: Crawler CAPTCHA failures
**Solution:** Check 2captcha/Anti-Captcha balance and API key

---

## 8. SSL Certificate

### Check Expiry
```bash
certbot certificates
```

### Renew Certificate
```bash
certbot renew
systemctl reload nginx
```

Current certificate expires: **2026-04-24**

---

## 9. Email Configuration

### AWS SES Settings
- Region: eu-central-1
- SMTP Host: email-smtp.eu-central-1.amazonaws.com
- SMTP Port: 587
- From Address: noreply@analize.online

### Test Email Sending
```bash
# From Python in /opt/healthy
python -c "
from backend_v2.services.email_service import get_email_service
es = get_email_service()
print('Configured:', es.is_configured())
"
```

---

## 10. Scheduled Jobs

### Active Scheduler Jobs
| Job | Interval | Purpose |
|-----|----------|---------|
| Provider Sync Check | 30 min | Check for new documents |
| Document Processing | 2 min | Process uploaded PDFs |
| Cleanup Limbo Docs | 1 hour | Clean stuck documents |
| Duplicate Removal | 6 hours | Remove duplicate docs |

### View Scheduler Status
```bash
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  https://analize.online/api/admin/scheduler-status
```

---

## 11. Emergency Procedures

### Complete Service Outage
```bash
# 1. Check server is accessible
ping 62.171.163.23

# 2. SSH and check services
ssh root@62.171.163.23
systemctl status healthy-api postgresql nginx

# 3. Check logs for errors
journalctl -u healthy-api -n 100

# 4. Restart services
systemctl restart healthy-api
# Wait 10 seconds
curl -X POST https://analize.online/api/admin/vault/unlock ...
```

### Database Corruption
```bash
# 1. Stop API
systemctl stop healthy-api

# 2. Restore from backup
PGPASSWORD=HealthyDB123 psql -h localhost -U healthy -d healthy < /opt/healthy/backups/LATEST_BACKUP.sql

# 3. Restart
systemctl start healthy-api
```

### Security Incident
1. Lock vault: `curl -X POST .../admin/vault/lock`
2. Disable API: `systemctl stop healthy-api`
3. Review logs: `journalctl -u healthy-api --since "1 hour ago"`
4. Check for unauthorized access in database

---

## 12. Contact Information

### Support
- GitHub Issues: https://github.com/dragusinb/healthy/issues

### External Services
- Contabo VPS: https://my.contabo.com
- AWS SES: https://console.aws.amazon.com
- Netopia: https://admin.netopia-payments.com
- 2captcha: https://2captcha.com

---

## 13. Key File Locations

| File | Location | Purpose |
|------|----------|---------|
| API Code | `/opt/healthy/backend_v2/` | FastAPI application |
| Frontend | `/opt/healthy/frontend_v2/dist/` | Built React app |
| Environment | `/opt/healthy/.env` | Configuration |
| Backups | `/opt/healthy/backups/` | Database backups |
| Nginx Config | `/etc/nginx/sites-available/healthy` | Web server |
| Systemd Unit | `/etc/systemd/system/healthy-api.service` | Service config |
| SSL Certs | `/etc/letsencrypt/live/analize.online/` | HTTPS certs |

---

## 14. Version Information

- **Python:** 3.11+
- **Node.js:** 18+
- **PostgreSQL:** 14+
- **FastAPI:** Latest
- **React:** 19
- **Playwright:** Latest (for crawlers)

---

*Keep this document updated when making infrastructure changes.*
