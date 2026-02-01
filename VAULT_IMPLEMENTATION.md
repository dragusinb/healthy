# Vault Security Implementation

## Status: IN PROGRESS
**Started:** 2026-02-01
**Last Updated:** 2026-02-01

## Overview
Implement a server-side encryption vault that:
- Keeps encryption keys in memory only (lost on reboot)
- Requires admin to enter master password after server restart
- Encrypts all sensitive data (credentials, documents, biomarkers, reports)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SERVER MEMORY                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 VAULT (in-memory)                    │    │
│  │  - master_key_hash (for verification)                │    │
│  │  - credentials_key (AES-256)                         │    │
│  │  - documents_key (AES-256)                           │    │
│  │  - is_unlocked: bool                                 │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     POSTGRESQL                               │
│  - users (vault_salt, master_key_hash - for unlock verify)  │
│  - linked_accounts (username_enc, password_enc)             │
│  - biomarkers (value_enc, numeric_value_enc)                │
│  - health_reports (content_enc)                             │
│  - user_profiles (full_name_enc, dob_enc, cnp_enc)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     FILESYSTEM                               │
│  data/encrypted/{user_id}/{doc_id}.enc                      │
│  (PDF files encrypted with documents_key)                   │
└─────────────────────────────────────────────────────────────┘
```

## Task Checklist

### Phase 1: Core Vault Service
- [x] Create `backend_v2/services/vault.py` - in-memory vault with encryption
- [x] Implement key derivation (PBKDF2)
- [x] Implement AES-256-GCM encrypt/decrypt
- [x] Implement vault lock/unlock/status methods
- [x] Store master key hash in database for verification

### Phase 2: Database Schema
- [x] Create migration script for encrypted columns
- [x] Add to `linked_accounts`: `username_enc`, `password_enc`
- [x] Add to `biomarkers`: `value_enc`, `numeric_value_enc`
- [x] Add to `health_reports`: `content_enc`
- [x] Add to `user_profiles`: `full_name_enc`, `dob_enc`, `cnp_enc`
- [x] Add `vault_config` table for salt and master key hash

### Phase 3: API Endpoints
- [x] POST `/admin/vault/unlock` - unlock vault with master password
- [x] POST `/admin/vault/lock` - lock vault
- [x] GET `/admin/vault/status` - check if vault is unlocked
- [x] POST `/admin/vault/initialize` - first-time setup with master password
- [x] Add vault check middleware to protected endpoints

### Phase 4: Update Existing Services
- [x] Update `users.py` router - encrypt/decrypt credentials and profile
- [x] Update `dashboard.py` router - decrypt biomarker values
- [x] Update `health.py` router - encrypt/decrypt report content
- [x] Update `documents.py` router - encrypt/decrypt PDF files

### Phase 5: Frontend Updates ✓
- [x] Create Vault Unlock page (shown when vault is locked)
- [x] Add vault status indicator to Admin panel
- [x] Handle 503 "Vault locked" responses gracefully
- [x] Add Lock Vault button to Admin panel

### Phase 6: Data Migration
- [x] Create migration script to encrypt existing data
- [ ] Run migration on production (MANUAL - requires master password)
- [ ] Verify all data accessible after migration
- [ ] Remove old unencrypted columns (after verification)

### Phase 7: Testing & Documentation
- [ ] Test vault lock/unlock flow
- [ ] Test all encrypted data operations
- [ ] Test server restart scenario
- [x] Update CLAUDE.md with vault instructions
- [x] Document vault recovery procedures

## Files Created/Modified

### New Files
- `backend_v2/services/vault.py` - Core vault service
- `backend_v2/routers/vault.py` - Vault API endpoints
- `backend_v2/migrations/add_encrypted_columns.py` - DB migration
- `backend_v2/migrations/migrate_to_encrypted.py` - Data migration
- `frontend_v2/src/pages/VaultUnlock.jsx` - Unlock UI

### Modified Files
- `backend_v2/main.py` - Add vault router, middleware
- `backend_v2/models.py` - Add encrypted columns
- `backend_v2/routers/linked_accounts.py` - Use vault encryption
- `backend_v2/routers/documents.py` - Encrypt PDF files
- `backend_v2/routers/health.py` - Encrypt reports
- `backend_v2/routers/dashboard.py` - Decrypt biomarkers
- `frontend_v2/src/App.jsx` - Add vault unlock route
- `frontend_v2/src/pages/Admin.jsx` - Vault status/lock button

## Security Notes

1. **Master Password Requirements**
   - Minimum 16 characters
   - Must be entered after every server restart
   - Hash stored in DB, actual password never stored

2. **Key Derivation**
   - PBKDF2 with SHA-256
   - 600,000 iterations (OWASP recommendation)
   - Unique salt per installation

3. **Encryption**
   - AES-256-GCM (authenticated encryption)
   - Unique nonce per encryption operation
   - Keys derived from master password

4. **When Vault is Locked**
   - All sensitive data inaccessible
   - Sync jobs return early (no-op)
   - API returns 503 with "Vault locked" message
   - Frontend shows unlock prompt

## Recovery Procedures

### Forgot Master Password
- **There is no recovery** - this is by design
- All encrypted data becomes permanently inaccessible
- Must reset system and re-import all data from providers

### Server Crash During Operation
- Vault automatically locks (keys lost from memory)
- No data corruption (encryption is atomic)
- Admin must unlock after restart

## Current Progress

**Last completed task:** Phase 5 - Frontend Updates (Vault status and Lock button added to Admin panel)
**Next task:** Phase 6 - Run migration on production (requires master password)

## Commands

```bash
# Run database migration (add encrypted columns)
cd /opt/healthy
python -m backend_v2.migrations.add_encrypted_columns

# Initialize vault (first time only)
curl -X POST https://analize.online/api/admin/vault/initialize \
  -H "Content-Type: application/json" \
  -d '{"master_password": "your-secure-password-here"}'

# Unlock vault (after every restart)
curl -X POST https://analize.online/api/admin/vault/unlock \
  -H "Content-Type: application/json" \
  -d '{"master_password": "your-secure-password-here"}'

# Check vault status
curl https://analize.online/api/admin/vault/status

# Migrate existing data to encrypted format
cd /opt/healthy
python -m backend_v2.migrations.migrate_to_encrypted
# (will prompt for master password)
```
