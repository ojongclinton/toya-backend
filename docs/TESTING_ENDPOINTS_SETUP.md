# Testing Endpoints Setup Guide

## Quick Start

To enable testing endpoints for frontend development:

### 1. Set the Environment Variable

**Option A: Using .env file (Recommended)**
```bash
# Add to your .env file
ENABLE_TESTING_ENDPOINTS=true
```

**Option B: Export in terminal**
```bash
# Linux/Mac
export ENABLE_TESTING_ENDPOINTS=true

# Windows CMD
set ENABLE_TESTING_ENDPOINTS=true

# Windows PowerShell
$env:ENABLE_TESTING_ENDPOINTS="true"
```

**Option C: Directly in settings (Not recommended)**
```python
# In core/settings.py (line ~299)
ENABLE_TESTING_ENDPOINTS = True  # Change from os.environ.get(...)
```

### 2. Restart Django Server
```bash
python manage.py runserver
```

### 3. Verify It's Working
```bash
# Test with curl (replace with your token)
curl -X POST http://localhost:8000/clients/dev/reset/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Should return success, not 403 Forbidden
```

---

## What This Flag Controls

When `ENABLE_TESTING_ENDPOINTS=true`, these endpoints become available:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/clients/dev/reset/` | POST | Reset client account (clear all data) |
| `/clients/delete/` | DELETE | Permanently delete client account |
| `/drivers/dev/reset/` | POST | Reset driver account (clear all data) |
| `/drivers/dev/adjust-wallet/` | POST | Set driver wallet to any amount |
| `/drivers/delete/` | DELETE | Permanently delete driver account |

---

## Security Implications

### ⚠️ Why This Flag Exists

These endpoints are **extremely destructive** and bypass normal business logic:
- Delete user accounts and all related data
- Modify financial balances arbitrarily
- Clear transaction history
- Remove payment records

### 🔴 Production Safety

**Default State:** `False` (disabled)
- Even if you forget to set it, endpoints are disabled by default
- Independent from `DEBUG` setting
- Must be explicitly enabled

**In Production:**
- MUST be `False` or not set
- Endpoints will return `403 Forbidden`
- No risk of accidental data loss

**In Development:**
- Set to `True` only when actively testing
- Can be toggled on/off as needed
- Doesn't affect other Django functionality

---

## Environment-Specific Configuration

### Local Development
```bash
# .env.local
DEBUG=True
ENABLE_TESTING_ENDPOINTS=true  # ✅ OK for local testing
```

### Staging Environment
```bash
# .env.staging
DEBUG=True
ENABLE_TESTING_ENDPOINTS=true  # ⚠️ OK if isolated, use with caution
```

### Production Environment
```bash
# .env.production
DEBUG=False
ENABLE_TESTING_ENDPOINTS=false  # 🔴 MUST BE FALSE
# Or simply don't set it (defaults to False)
```

---

## Checking Current Status

### Method 1: Django Shell
```python
python manage.py shell

>>> from django.conf import settings
>>> settings.ENABLE_TESTING_ENDPOINTS
False  # or True
```

### Method 2: Test Endpoint
```bash
# Try calling a testing endpoint
curl -X POST http://localhost:8000/clients/dev/reset/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# If disabled, you'll get:
# {"Message": "This endpoint is only available when ENABLE_TESTING_ENDPOINTS is True."}
```

### Method 3: Check Settings File
```bash
# Look at line ~299 in core/settings.py
grep -n "ENABLE_TESTING_ENDPOINTS" core/settings.py
```

---

## Common Scenarios

### Scenario 1: Frontend Developer Testing
```bash
# Morning: Enable testing endpoints
echo "ENABLE_TESTING_ENDPOINTS=true" >> .env
python manage.py runserver

# Test all day with reset/delete endpoints

# Evening: Disable for safety
sed -i 's/ENABLE_TESTING_ENDPOINTS=true/ENABLE_TESTING_ENDPOINTS=false/' .env
```

### Scenario 2: CI/CD Pipeline
```yaml
# .github/workflows/test.yml
env:
  ENABLE_TESTING_ENDPOINTS: true  # OK in test environment
  
# .github/workflows/deploy-prod.yml
env:
  ENABLE_TESTING_ENDPOINTS: false  # MUST be false for production
```

### Scenario 3: Docker Development
```dockerfile
# docker-compose.dev.yml
environment:
  - ENABLE_TESTING_ENDPOINTS=true

# docker-compose.prod.yml
environment:
  - ENABLE_TESTING_ENDPOINTS=false
```

---

## Troubleshooting

### Problem: Endpoints still return 403
**Solutions:**
1. Check .env file has `ENABLE_TESTING_ENDPOINTS=true`
2. Restart Django server after changing .env
3. Verify environment variable is loaded:
   ```python
   import os
   print(os.environ.get('ENABLE_TESTING_ENDPOINTS'))
   ```
4. Check for typos in variable name

### Problem: Can't find where to set it
**Location:** `core/settings.py` line ~299
```python
ENABLE_TESTING_ENDPOINTS = os.environ.get('ENABLE_TESTING_ENDPOINTS', 'False').lower() in ('true', '1', 'yes')
```

### Problem: Need to enable temporarily
```bash
# Enable for this session only (doesn't modify .env)
ENABLE_TESTING_ENDPOINTS=true python manage.py runserver
```

---

## Best Practices

✅ **DO:**
- Enable only when actively testing
- Use .env file for configuration
- Document when you enable it
- Disable after testing session
- Use version control for .env.example

❌ **DON'T:**
- Commit .env with `true` value
- Enable in production
- Leave enabled permanently
- Hardcode `True` in settings.py
- Share .env files with sensitive data

---

## Related Documentation

- Full endpoint documentation: `docs/DEVELOPMENT_ENDPOINTS.md`
- Settings configuration: `core/settings.py` (lines 272-299)
- Example configuration: `.env.example`

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│  ENABLE_TESTING_ENDPOINTS Quick Reference               │
├─────────────────────────────────────────────────────────┤
│  Enable:  ENABLE_TESTING_ENDPOINTS=true                 │
│  Disable: ENABLE_TESTING_ENDPOINTS=false                │
│  Default: false (safe by default)                       │
│                                                          │
│  Location: .env file or environment variables           │
│  Restart required: Yes (restart Django server)          │
│                                                          │
│  Production: MUST BE FALSE ⚠️                           │
│  Development: Can be true for testing                   │
└─────────────────────────────────────────────────────────┘
```
