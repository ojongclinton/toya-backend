# Wallet Recharge Flow - Bug Fix Documentation

## Problem Description

When drivers recharged their wallet via USSD (S3 Mobile Pay), the wallet balance (`wallet_money`) was not being updated properly, even though the payment transaction was marked as successful.

## Root Cause Analysis

The issue was in the payment processing flow:

1. **Race Condition Risk**: The `payment.py` file was checking the transaction status before calling `WalletService.process_deposit_success()`, but it wasn't using database locks, which could cause race conditions when the WebSocket consumer polls every 20 seconds.

2. **Missing Database Locks**: The `WalletService.process_deposit_success()` method wasn't using `select_for_update()` to lock the payment record, allowing potential duplicate processing.

3. **Insufficient Logging**: There was minimal logging to debug wallet update failures.

4. **No Real-time Feedback**: Drivers had no WebSocket notification when their wallet was successfully recharged.

## Solution Implemented

### 1. Enhanced Payment Processing (`payments/payment.py`)

**Changes:**
- Moved duplicate check to the beginning of `launch_process()` method
- Added `driver.refresh_from_db()` after wallet update to ensure latest balance
- Enhanced error handling with transaction rollback on failure
- Improved notification message to include amount and new balance
- Added comprehensive logging

**Key Code:**
```python
# Check if already processed to prevent duplicate processing
if transaction.payments_status == 'completed':
    logger.info(f"Transaction {transaction_id} already completed, skipping")
    return

# Refresh driver to get updated wallet balance
driver.refresh_from_db()

# Enhanced notification with balance info
message=f"Votre dépôt de {transaction_amount} FCFA a été effectué avec succès. Nouveau solde: {driver.wallet_money} FCFA"
```

### 2. Improved Wallet Service (`payments/services/wallet_service.py`)

**Changes:**
- Added `select_for_update()` to lock payment record and prevent race conditions
- Added double-check for already completed transactions
- Added `driver.refresh_from_db()` to get current balance with lock
- Used `update_fields` parameter in `save()` for better performance
- Added comprehensive logging at each step
- Added WebSocket notification for real-time wallet updates

**Key Code:**
```python
# Lock the payment record to prevent race conditions
payment = PaymentsDrivers.objects.select_for_update().get(id=transaction_id)

# Double-check if already processed
if payment.payments_status == 'completed':
    logger.warning(f"Payment {transaction_id} already completed, skipping")
    return

# Get current balance with lock
driver.refresh_from_db()
balance_before = driver.wallet_money
balance_after = balance_before + amount

# Update with specific fields only
driver.save(update_fields=['wallet_money'])
payment.save(update_fields=['payments_status'])
```

### 3. WebSocket Real-time Updates

**Added WebSocket notification** to inform drivers immediately when their wallet is recharged:

```python
channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    f'ride_updates_{driver.id}',
    {
        'type': 'wallet_update',
        'message': {
            'event_type': 'wallet_deposit',
            'transaction_id': str(payment.id),
            'amount': float(amount),
            'balance_before': float(balance_before),
            'balance_after': float(balance_after),
            'payment_method': payment.payments_method,
            'timestamp': wallet_tx.created_at.isoformat()
        }
    }
)
```

**Updated WebSocket Consumer** (`rides/consumers.py`) to handle wallet updates:

```python
async def wallet_update(self, event):
    """Handler for wallet balance updates."""
    await self.send(text_data=json.dumps({
        'type': 'wallet_update',
        'event_type': event['message'].get('event_type'),
        'transaction_id': event['message'].get('transaction_id'),
        'amount': event['message'].get('amount'),
        'balance_before': event['message'].get('balance_before'),
        'balance_after': event['message'].get('balance_after'),
        'payment_method': event['message'].get('payment_method'),
        'timestamp': event['message'].get('timestamp')
    }, ensure_ascii=False))
```

## Testing the Fix

### 1. Manual Testing via API

```bash
# Step 1: Check current wallet balance
GET /api/payments/wallet/history
Authorization: Bearer <driver_token>

# Step 2: Initiate wallet deposit
POST /api/payments/wallet/make-deposit
Authorization: Bearer <driver_token>
Content-Type: application/json

{
  "amount": 5000,
  "payment_method": "orange_money",
  "phone_number": "+237XXXXXXXXX"
}

# Response will include transaction_id
{
  "Message": "Deposit initialize successfull.",
  "data": {
    "transaction_id": "uuid-here"
  }
}

# Step 3: Connect to WebSocket for real-time updates
ws://domain/ws/payment/status/<transaction_id>/<user_id>/

# Step 4: Complete USSD payment on phone
# Dial the USSD code and enter PIN

# Step 5: Verify wallet balance updated
GET /api/payments/wallet/history
Authorization: Bearer <driver_token>

# Should show increased balance
```

### 2. Automated Testing

Run the existing test suite:

```bash
# Run wallet deposit tests
pytest payments/tests/test_wallet_deposit.py -v

# Run wallet service tests
pytest payments/tests/test_wallet_service.py -v

# Expected output: All tests should pass
```

### 3. WebSocket Testing

Connect to the ride status WebSocket to receive wallet updates:

```javascript
// Frontend integration
const ws = new WebSocket('ws://domain/ws/ride-status/');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'wallet_update') {
    console.log('Wallet updated!');
    console.log('Event:', data.event_type);
    console.log('Amount:', data.amount, 'FCFA');
    console.log('New Balance:', data.balance_after, 'FCFA');
    
    // Update UI with new balance
    updateWalletBalance(data.balance_after);
  }
};
```

## Verification Checklist

After deploying the fix, verify:

- [ ] Wallet balance updates correctly after USSD payment
- [ ] `WalletTransaction` record is created with correct amounts
- [ ] `PaymentsDrivers` status changes from `in_pending` to `completed`
- [ ] Driver receives notification about successful deposit
- [ ] WebSocket sends real-time wallet update
- [ ] No duplicate processing occurs if payment status is checked multiple times
- [ ] Logs show detailed information about wallet updates
- [ ] Database transactions are atomic (all-or-nothing)

## Monitoring

Check logs for successful wallet updates:

```bash
# Look for these log messages
grep "Deposit processed successfully" /var/log/django/app.log
grep "Updated driver .* wallet_money to" /var/log/django/app.log
grep "WebSocket notification sent for wallet deposit" /var/log/django/app.log
```

## Rollback Plan

If issues occur, the changes are backward compatible. The old flow will still work, but with the improvements:
- Better logging helps identify issues
- Database locks prevent race conditions
- WebSocket notifications are optional (won't break if channel layer fails)

## Related Files Modified

1. `payments/payment.py` - Enhanced payment processing logic
2. `payments/services/wallet_service.py` - Improved wallet update with locks and logging
3. `rides/consumers.py` - Added wallet_update handler for WebSocket

## Performance Impact

- **Positive**: Using `update_fields` reduces database write overhead
- **Positive**: `select_for_update()` prevents race conditions
- **Neutral**: WebSocket notifications add minimal overhead
- **Positive**: Better logging helps identify issues faster

## Security Considerations

- Database locks prevent double-crediting
- Transaction atomicity ensures data consistency
- WebSocket uses existing authentication (user-specific channels)
- No sensitive data exposed in WebSocket messages

## Future Improvements

1. Add retry mechanism for failed WebSocket notifications
2. Implement webhook endpoint for S3 Mobile Pay callbacks (instead of polling)
3. Add wallet transaction history pagination
4. Create admin dashboard for monitoring wallet transactions
5. Add alerts for suspicious wallet activity
