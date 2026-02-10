# Healthy - Backlog & Future Work

**Last Updated:** 2026-02-10

> For current phase status, see `CLAUDE.md`
> For completed work history, see `tasks.md`

---

## Phase Status Summary

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 0: MVP | COMPLETE | 100% |
| Phase 1: Biomarkers | COMPLETE | 100% |
| Phase 2: Multi-User & AI | COMPLETE | 100% |
| Phase 3: Mobile & Monetization | PARTIAL | 70% |
| Phase 4: Production | COMPLETE | 90% |

---

## Remaining Work

### Phase 3 Completion (Mobile & Monetization)

**Subscriptions & Payments:**
- [x] Subscription tiers (Free/Premium/Family)
- [x] Netopia payment integration
- [x] Usage tracking and limits
- [ ] Stripe integration (for international users)
- [ ] Invoice generation/download

**Mobile App:**
- [x] Push notification infrastructure (Web Push)
- [ ] React Native mobile app
- [ ] App Store / Google Play submission
- [ ] Offline data access

**Family Features:**
- [x] Family groups creation
- [x] Family member data sharing
- [x] Family health dashboard
- [x] Invite system with codes

### Phase 4 Polish

**Already Complete:**
- [x] PostgreSQL database
- [x] Contabo VPS deployment
- [x] Nginx reverse proxy + SSL/HTTPS
- [x] Systemd services
- [x] Domain: analize.online
- [x] GDPR compliance (export, deletion, consent)
- [x] Monitoring (Prometheus + Grafana)
- [x] Database backups (daily pg_dump)

**Optional Improvements:**
- [ ] Load balancing (when traffic requires)
- [ ] CDN for static assets
- [ ] Redis for rate limiting (multi-worker)
- [ ] CI/CD pipeline (GitHub Actions)

---

## Technical Debt (Low Priority)

| Item | Severity | Notes |
|------|----------|-------|
| Bare except clauses | Medium | 16 instances in crawlers |
| Crawler code duplication | Medium | Extract to base class |
| React useEffect cleanup | Low | Add AbortController |
| Console statements | Low | Replace with error tracking |

---

## Feature Ideas (Future)

- B2B white-label for clinics
- Integration with wearables (Apple Health, Fitbit)
- Predictive health alerts using AI
- Multi-language support beyond RO/EN
- Export health reports as PDF
- Share reports with doctors via secure link

---

## Infrastructure Resources

**Current Server (Contabo VPS):**
- IP: 62.171.163.23
- Services: healthy-api, xvfb, nginx, postgresql
- Monitoring: Prometheus + Grafana

**Monitoring URLs:**
- Grafana: https://analize.online/grafana/
- Health Check: https://analize.online/api/health

**Useful Commands:**
```bash
# Check services
systemctl status healthy-api postgresql nginx

# View logs
journalctl -u healthy-api -n 100 -f

# Database stats
PGPASSWORD=HealthyDB123 psql -h localhost -U healthy -d healthy \
  -c "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM documents;"
```

---

*This file tracks future work. For current status see CLAUDE.md.*
