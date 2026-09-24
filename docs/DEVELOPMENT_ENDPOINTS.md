# Development & Testing Endpoints

## Overview
These endpoints are designed to facilitate frontend testing and development. They are **ONLY available when `DEBUG=True`** in Django settings and will return `403 Forbidden` in production.

---

## Client Endpoints

### 1. Reset Client Account
**Endpoint:** `POST /clients/dev/reset/`  
**Authentication:** Required (Bearer Token)  
**Purpose:** Reset client account to initial state without deleting it

**What it does:**
- Clears all rides, payments, support tickets, conversations, notifications
- Clears referrals and promotions
- Resets `is_phone_verified` to `False`
- Keeps account credentials (phone, email, password)

**Response:**
```json
{
  "Message": "Client account reset successfully. All related data cleared.",
  "Details": {
    "phone_verified": false,
    "account_status": "reset"
  }
}
```

**Use case:** Test signup/verification flows repeatedly without re-registering

---

### 2. Delete Client Account
**Endpoint:** `DELETE /clients/delete/`  
**Authentication:** Required (Bearer Token)  
**Purpose:** Permanently delete client account and all related data

**What it does:**
- Deletes all related data (rides, payments, support, etc.)
- Permanently removes the account
- Frees up phone number for re-registration

**Response:**
```json
{
  "Message": "Client account and all related data deleted successfully"
}
```

**Use case:** Complete cleanup when you need to test full registration flow

---

## Driver Endpoints

### 1. Reset Driver Account
**Endpoint:** `POST /drivers/dev/reset/`  
**Authentication:** Required (Bearer Token)  
**Purpose:** Reset driver account to initial state without deleting it

**What it does:**
- Clears all rides, payments, vehicles, subscriptions, support tickets
- Clears conversations, notifications, referrals
- Resets `is_phone_verified` to `False`
- Resets `wallet_money` to `0`
- Resets `is_available` to `False`
- Keeps account credentials

**Response:**
```json
{
  "Message": "Driver account reset successfully. All related data cleared.",
  "Details": {
    "phone_verified": false,
    "wallet_balance": 0,
    "is_available": false,
    "account_status": "reset"
  }
}
```

**Use case:** Test driver flows repeatedly without re-registering

---

### 2. Adjust Driver Wallet
**Endpoint:** `POST /drivers/dev/adjust-wallet/`  
**Authentication:** Required (Bearer Token)  
**Purpose:** Set driver wallet balance to any amount for testing

**Request Body:**
```json
{
  "amount": 5000
}
```

**Response:**
```json
{
  "Message": "Wallet balance adjusted successfully.",
  "old_balance": 0,
  "new_balance": 5000
}
```

**Use case:** Test payment flows, withdrawals, ride earnings without actual transactions

---

### 3. Delete Driver Account
**Endpoint:** `DELETE /drivers/delete/`  
**Authentication:** Required (Bearer Token)  
**Purpose:** Permanently delete driver account and all related data

**What it does:**
- Deletes all related data (rides, payments, vehicles, subscriptions, etc.)
- Permanently removes the account
- Frees up phone number for re-registration

**Response:**
```json
{
  "Message": "Driver account and all related data deleted successfully"
}
```

**Use case:** Complete cleanup when you need to test full registration flow

---

## Safety Features

### 1. ENABLE_TESTING_ENDPOINTS Flag
All endpoints check `settings.ENABLE_TESTING_ENDPOINTS`:
- ✅ **Testing Enabled (`ENABLE_TESTING_ENDPOINTS=True`)**: Endpoints work normally
- ❌ **Testing Disabled (`ENABLE_TESTING_ENDPOINTS=False`)**: Returns `403 Forbidden`

**How to enable:**
```bash
# Option 1: Environment variable (recommended)
export ENABLE_TESTING_ENDPOINTS=true

# Option 2: In .env file
ENABLE_TESTING_ENDPOINTS=true

# Option 3: Directly in core/settings.py (not recommended)
ENABLE_TESTING_ENDPOINTS = True
```

**⚠️ CRITICAL: This flag MUST be False in production!**
- Default value is `False` for safety
- Independent from `DEBUG` setting
- Explicitly controls destructive testing operations

### 2. Error Handling
All endpoints include comprehensive error handling:
- `404 Not Found`: User doesn't exist
- `400 Bad Request`: Invalid parameters
- `500 Internal Server Error`: Unexpected errors with details

---

## Testing Workflow Examples

### Example 1: Test Client Signup Flow Multiple Times
```bash
# 1. Register client
POST /clients/auth/register/

# 2. Test OTP verification
POST /clients/auth/verify-signup-otp/

# 3. Test some rides...

# 4. Reset account (keeps phone number)
POST /clients/dev/reset/
Authorization: Bearer <token>

# 5. Test OTP flow again with same account
POST /clients/auth/request-signup-otp/
```

### Example 2: Test Driver Payment Flows
```bash
# 1. Login as driver
POST /drivers/auth/login/

# 2. Set wallet to 10000 for testing
POST /drivers/dev/adjust-wallet/
Authorization: Bearer <token>
Body: {"amount": 10000}

# 3. Test withdrawal flows...

# 4. Reset wallet to 0
POST /drivers/dev/adjust-wallet/
Body: {"amount": 0}
```

### Example 3: Clean Slate Testing
```bash
# 1. Complete delete (frees phone number)
DELETE /clients/delete/
Authorization: Bearer <token>

# 2. Register new account with same phone
POST /clients/auth/register/
Body: {"phone_number": "+237697200001", ...}
```

---

## Important Notes

1. **Production Safety**: These endpoints are completely disabled in production
2. **Authentication Required**: All endpoints require valid JWT token
3. **Cascade Deletion**: Delete endpoints handle all foreign key relationships properly
4. **No Data Loss in Reset**: Reset keeps the account, only clears related data
5. **Wallet Adjustment**: Only for drivers, accepts any integer value

---

## Frontend Integration

### JavaScript/TypeScript Example
```javascript
// Reset client account
async function resetClientAccount(token) {
  const response = await fetch('http://localhost:8000/clients/dev/reset/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
}

// Adjust driver wallet
async function adjustDriverWallet(token, amount) {
  const response = await fetch('http://localhost:8000/drivers/dev/adjust-wallet/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ amount })
  });
  return response.json();
}

// Delete account
async function deleteAccount(token, userType) {
  const endpoint = userType === 'client' 
    ? 'http://localhost:8000/clients/delete/'
    : 'http://localhost:8000/drivers/delete/';
    
  const response = await fetch(endpoint, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
}
```

---

## Troubleshooting

### "This endpoint is only available when ENABLE_TESTING_ENDPOINTS is True"
- **Cause**: `ENABLE_TESTING_ENDPOINTS=False` in settings (default)
- **Solution**: Set `ENABLE_TESTING_ENDPOINTS=true` in your `.env` file or environment variables
- **Check current value**: Look in `core/settings.py` line ~299

### "Account deletion is disabled"
- **Cause**: `ENABLE_TESTING_ENDPOINTS=False` in settings
- **Solution**: Enable the flag as described above

### "Client/Driver not found"
- **Cause**: Token doesn't match any user
- **Solution**: Ensure you're using a valid authentication token

### Foreign Key Constraint Errors
- **Cause**: Database relationships not properly handled
- **Solution**: These endpoints handle all cascades - report if you see this error

---

## API Documentation
All endpoints are documented in the Swagger/OpenAPI schema:
- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/api/schema/redoc/`
- Look for tags: `Clients - Development` and `Drivers - Development`
