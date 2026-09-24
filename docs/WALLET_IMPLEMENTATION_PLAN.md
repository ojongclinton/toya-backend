# 💰 Wallet Management Implementation Plan

**Project:** ELYFT Toya Backend  
**Focus:** Wallet refactoring with grade-based commission system  
**Priority:** HIGH - Core payment functionality  
**Estimated Time:** 3-4 hours  

---

## 🎯 **Objective**

Refactor wallet management to:
- Use grade-based commission rates (not hardcoded percentages)
- Implement proper transaction tracking
- Ensure atomic operations (no partial completions)
- Maintain flexibility for future changes

---

## 💡 **Use Case Flow Overview**

### **1. DRIVER ONBOARDING & WALLET INITIALIZATION**
```
Driver registers → Wallet created with 0.00 FCFA balance
Driver assigned Bronze grade (20% commission) by default
```

### **2. WALLET DEPOSIT (Money IN)**
```
Driver needs funds to accept rides
↓
Driver initiates deposit (e.g., 10,000 FCFA via Orange Money)
↓
Payment processed through S3 Mobile Pay
↓
On SUCCESS:
  - WalletTransaction created (type: "deposit")
  - Balance updated: 0.00 → 10,000.00 FCFA
  - Driver receives notification
```

### **3. RIDE ACCEPTANCE (Pre-Authorization Check)**
```
Client requests ride (5,000 FCFA)
↓
Driver attempts to accept ride
↓
System checks:
  - Get driver's current grade (e.g., Bronze = 20%)
  - Calculate required commission: 5,000 × 20% = 1,000 FCFA
  - Check wallet balance: 10,000 FCFA ≥ 1,000 FCFA ✅
↓
If SUFFICIENT: Ride accepted, driver proceeds
If INSUFFICIENT: Error returned, ride not accepted
```

### **4. RIDE EXECUTION**
```
Driver picks up client → Status: "in_progress"
Driver drives to destination
(Commission NOT deducted yet - still in wallet)
```

### **5. RIDE COMPLETION (Money OUT - Commission Deduction)**
```
Driver arrives at destination
↓
Driver clicks "Complete Ride"
↓
ATOMIC TRANSACTION begins:
  ├─ Update ride status: "in_progress" → "completed"
  ├─ Calculate commission:
  │   - Gross amount: 5,000 FCFA
  │   - Commission (20%): 1,000 FCFA
  │   - Net earning: 4,000 FCFA
  ├─ Deduct commission from wallet:
  │   - Balance before: 10,000 FCFA
  │   - Balance after: 9,000 FCFA
  ├─ Create WalletTransaction (type: "commission_deduction")
  ├─ Create PaymentsDrivers records (for backward compatibility)
  ├─ Mark driver available
  └─ Send notifications
↓
If ALL SUCCESS: Return success response
If ANY FAILURE: Rollback everything, ride stays "in_progress"
```

### **6. INSUFFICIENT WALLET SCENARIO**
```
Driver completes ride but wallet has only 500 FCFA
Required commission: 1,000 FCFA
↓
System prevents completion:
  - Ride stays "in_progress"
  - Error message: "Insufficient wallet balance"
  - Driver must deposit funds before completing
```

### **7. GRADE UPGRADE IMPACT**
```
Driver performs well → Upgraded to Silver (19% commission)
↓
Next ride (5,000 FCFA):
  - Required at acceptance: 950 FCFA (instead of 1,000)
  - Deducted at completion: 950 FCFA (instead of 1,000)
  - Net earning: 4,050 FCFA (instead of 4,000)
```

### **8. TRANSACTION HISTORY & AUDIT**
```
Driver views wallet history:
  - All deposits (money IN)
  - All commission deductions (money OUT)
  - Balance before/after each transaction
  - Commission rate at time of transaction
  - Grade at time of transaction
```

### **🔑 Key Principles**

1. **Pre-Authorization**: Check wallet BEFORE accepting ride
2. **Deferred Deduction**: Commission deducted AFTER ride completion
3. **Atomic Operations**: All-or-nothing transactions (no partial states)
4. **Grade-Based**: Commission always uses driver's current grade
5. **Audit Trail**: Every wallet change creates a WalletTransaction record
6. **Fail-Safe**: Insufficient balance prevents completion, not acceptance

### **📊 Example Scenario**

**Initial State:**
- Driver: Bronze grade (20% commission)
- Wallet: 10,000 FCFA

**Ride 1:** 5,000 FCFA
- Acceptance check: ✅ (needs 1,000, has 10,000)
- Completion: -1,000 FCFA commission
- New balance: 9,000 FCFA

**Ride 2:** 8,000 FCFA
- Acceptance check: ✅ (needs 1,600, has 9,000)
- Completion: -1,600 FCFA commission
- New balance: 7,400 FCFA

**Ride 3:** 40,000 FCFA
- Acceptance check: ❌ (needs 8,000, has 7,400)
- Driver must deposit first

---

## ✅ **Task List**

### **PHASE 1: Critical Bug Fixes (1 hour)**

#### Task 1.1: Fix Ride Acceptance Validation ⏱️ 30 min
**File:** `rides/views.py` - function `driver_accept_rides()`  
**Current Issue:** Hardcoded 20% validation, doesn't use driver's actual grade commission

**Changes:**
```python
# BEFORE (line ~539-540):
ride_price = rides.final_price 
minimum_required_wallet = 0.2 * ride_price  # ❌ Hardcoded 20%

# AFTER:
from drivers.models import DriverGrade
from decimal import Decimal

# Get driver's current grade
driver_grade = DriverGrade.objects.filter(
    driver=driver, 
    is_current=True
).select_related('grade').first()

commission_rate = driver_grade.grade.commission_rate if driver_grade else Decimal('20.00')

# Calculate actual commission amount
ride_price = Decimal(str(rides.final_price))
commission_amount = (ride_price * commission_rate) / 100

# Check wallet balance
if driver.wallet_money < commission_amount:
    return Response({
        "Message": f"Solde wallet insuffisant. Vous avez besoin de {commission_amount} FCFA ({commission_rate}% commission) pour accepter cette course.",
        "required_amount": float(commission_amount),
        "current_balance": float(driver.wallet_money),
        "commission_rate": float(commission_rate)
    }, status=403)
```

**Testing:**
- [ ] Test with driver having Bronze grade (20% commission)
- [ ] Test with driver having Gold grade (18% commission)
- [ ] Test with insufficient wallet balance
- [ ] Verify error message shows correct commission rate

---

#### Task 1.2: Fix Commission Deduction Function ⏱️ 30 min
**File:** `payments/customs.py` - function `retrieve_a_wallet_driver_amount()`  
**Current Issue:** Uses hardcoded percentage=15 default, doesn't use grade

**Changes:**
```python
# BEFORE (line 50):
def retrieve_a_wallet_driver_amount(final_rides, driver_id, percentage=15):

# AFTER:
def retrieve_a_wallet_driver_amount(final_rides, driver_id, percentage=None):
    """
    Deduct commission from driver wallet after ride completion.
    Uses driver's grade commission rate if percentage not provided.
    """
    from drivers.models import Drivers, DriverGrade
    from decimal import Decimal
    
    drivers = Drivers.objects.get(id=driver_id)
    
    # Get commission rate from grade if not provided
    if percentage is None:
        driver_grade = DriverGrade.objects.filter(
            driver=drivers, 
            is_current=True
        ).select_related('grade').first()
        percentage = float(driver_grade.grade.commission_rate) if driver_grade else 20.0
    
    # Rest of existing logic...
```

**Testing:**
- [ ] Test commission deduction with different grades
- [ ] Verify correct commission amount calculated
- [ ] Test with insufficient wallet balance
- [ ] Verify exception is raised properly

---

### **PHASE 2: Transaction Model (1 hour)**

#### Task 2.1: Create WalletTransaction Model ⏱️ 30 min
**File:** `payments/models.py`  
**Purpose:** Track all wallet operations for audit trail and reconciliation

**Add to models.py:**
```python
from uuid import uuid4
from decimal import Decimal

TRANSACTION_TYPE = [
    # Money IN
    ("deposit", "Wallet Deposit"),
    ("ride_earning", "Ride Earning"),
    ("referral_bonus", "Referral Bonus"),
    ("admin_credit", "Admin Credit"),
    
    # Money OUT
    ("commission_deduction", "Commission Deduction"),
    ("subscription_fee", "Subscription Fee"),
    ("penalty", "Penalty"),
    ("admin_debit", "Admin Debit"),
]

TRANSACTION_STATUS = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]

class WalletTransaction(models.Model):
    """
    Records all wallet transactions for drivers.
    Provides audit trail and enables balance reconciliation.
    """
    id = models.UUIDField(primary_key=True, default=uuid4)
    driver = models.ForeignKey(
        'drivers.Drivers', 
        on_delete=models.CASCADE, 
        related_name='wallet_transactions'
    )
    
    # Transaction details
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    
    # References
    ride = models.ForeignKey(
        'rides.Rides', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='wallet_transactions'
    )
    payment = models.ForeignKey(
        'PaymentsDrivers', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )
    
    # Metadata
    description = models.TextField(blank=True)
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Commission rate at time of transaction"
    )
    grade_name = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="Driver grade at time of transaction"
    )
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=TRANSACTION_STATUS, 
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['driver', '-created_at']),
            models.Index(fields=['transaction_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.driver.id} - {self.transaction_type} - {self.amount} FCFA"
```

**Steps:**
- [ ] Add model to `payments/models.py`
- [ ] Run `python manage.py makemigrations payments`
- [ ] Review migration file
- [ ] Run `python manage.py migrate`
- [ ] Verify table created in database

---

#### Task 2.2: Update Drivers Model ⏱️ 15 min
**File:** `drivers/models.py`  
**Purpose:** Change wallet_money from IntegerField to DecimalField for precision

**Changes:**
```python
# BEFORE:
wallet_money = models.IntegerField(default=0, null=False)

# AFTER:
from decimal import Decimal

wallet_money = models.DecimalField(
    max_digits=12, 
    decimal_places=2, 
    default=Decimal('0.00'),
    help_text="Driver wallet balance in FCFA"
)
```

**Steps:**
- [ ] Update model field
- [ ] Run `python manage.py makemigrations drivers`
- [ ] Run `python manage.py migrate`
- [ ] Test existing wallet operations still work

---

#### Task 2.3: Create WalletTransaction Serializer ⏱️ 15 min
**File:** `payments/serializer.py`

**Add:**
```python
class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            'id',
            'transaction_type',
            'amount',
            'balance_before',
            'balance_after',
            'description',
            'commission_rate',
            'grade_name',
            'status',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
```

---

### **PHASE 3: Wallet Service Layer (1.5 hours)**

#### Task 3.1: Create WalletService Class ⏱️ 1 hour
**File:** `payments/services/wallet_service.py` (NEW FILE)  
**Purpose:** Centralize all wallet operations

**Create file structure:**
```
payments/
  ├── services/
  │   ├── __init__.py
  │   └── wallet_service.py
```

**wallet_service.py content:**
```python
"""
Wallet Service - Centralized wallet management
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
import logging

from drivers.models import Drivers, DriverGrade
from payments.models import WalletTransaction, PaymentsDrivers
from notifications.models import Notifications
from notifications.custums import RetrieveBackofficeUser

logger = logging.getLogger(__name__)


class WalletService:
    """
    Service for managing driver wallet operations.
    All wallet modifications should go through this service.
    """
    
    @staticmethod
    def get_driver_commission_rate(driver):
        """
        Get the current commission rate for a driver based on their grade.
        
        Args:
            driver: Drivers instance
            
        Returns:
            Decimal: Commission rate percentage
        """
        driver_grade = DriverGrade.objects.filter(
            driver=driver, 
            is_current=True
        ).select_related('grade').first()
        
        if driver_grade:
            return driver_grade.grade.commission_rate
        return Decimal('20.00')  # Default fallback
    
    @staticmethod
    def calculate_commission(ride_price, commission_rate):
        """
        Calculate commission amount for a ride.
        
        Args:
            ride_price: Decimal or float
            commission_rate: Decimal percentage
            
        Returns:
            tuple: (commission_amount, net_earning)
        """
        ride_price = Decimal(str(ride_price))
        commission_amount = (ride_price * commission_rate) / 100
        net_earning = ride_price - commission_amount
        
        return commission_amount, net_earning
    
    @staticmethod
    @transaction.atomic
    def process_ride_commission(ride, driver):
        """
        Process commission deduction after ride completion.
        Creates wallet transactions and updates balance.
        
        Args:
            ride: Rides instance
            driver: Drivers instance
            
        Returns:
            dict: Transaction details
            
        Raises:
            ValueError: If insufficient wallet balance
        """
        # Get driver's grade and commission rate
        driver_grade = DriverGrade.objects.filter(
            driver=driver, 
            is_current=True
        ).select_related('grade').first()
        
        commission_rate = driver_grade.grade.commission_rate if driver_grade else Decimal('20.00')
        grade_name = driver_grade.grade.name if driver_grade else 'Standard'
        
        # Calculate amounts
        gross_amount = Decimal(str(ride.final_price))
        commission_amount, net_earning = WalletService.calculate_commission(
            gross_amount, 
            commission_rate
        )
        
        balance_before = driver.wallet_money
        
        # Verify sufficient balance
        if balance_before < commission_amount:
            raise ValueError(
                f"Solde wallet insuffisant. Requis: {commission_amount} FCFA, "
                f"Disponible: {balance_before} FCFA"
            )
        
        # Deduct commission from wallet
        balance_after = balance_before - commission_amount
        
        # Create commission deduction transaction
        commission_tx = WalletTransaction.objects.create(
            driver=driver,
            transaction_type='commission_deduction',
            amount=commission_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            ride=ride,
            commission_rate=commission_rate,
            grade_name=grade_name,
            description=f"Commission ({commission_rate}%) pour course {ride.id}",
            status='completed'
        )
        
        # Update driver wallet balance
        driver.wallet_money = balance_after
        driver.save()
        
        # Create payment records (for backward compatibility)
        # Net earning record
        PaymentsDrivers.objects.create(
            driver_id=driver,
            amount=net_earning,
            payments_type='ride_payment',
            payments_status='completed'
        )
        
        # Commission record
        PaymentsDrivers.objects.create(
            driver_id=driver,
            amount=commission_amount,
            payments_type='wallet_pay',
            payments_status='completed'
        )
        
        # Send notification
        try:
            backoffice_user = RetrieveBackofficeUser().retrieve_backoffice_user(driver.id)
            Notifications.objects.create(
                sender=backoffice_user,
                recipient=driver,
                notification_type='withdraw_wallet',
                message=f"Commission de {commission_amount} FCFA ({commission_rate}%) déduite pour la course récente.",
                event_id=commission_tx.id
            )
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
        
        logger.info(
            f"Commission processed: Driver {driver.id}, "
            f"Ride {ride.id}, Amount {commission_amount} FCFA"
        )
        
        return {
            'commission_amount': commission_amount,
            'net_earning': net_earning,
            'commission_rate': commission_rate,
            'balance_after': balance_after,
            'transaction_id': str(commission_tx.id)
        }
    
    @staticmethod
    @transaction.atomic
    def process_deposit_success(transaction_id):
        """
        Process successful wallet deposit from S3 Mobile Pay.
        
        Args:
            transaction_id: PaymentsDrivers transaction ID
        """
        payment = PaymentsDrivers.objects.get(id=transaction_id)
        driver = payment.driver_id
        amount = Decimal(str(payment.amount))
        
        balance_before = driver.wallet_money
        balance_after = balance_before + amount
        
        # Create deposit transaction
        WalletTransaction.objects.create(
            driver=driver,
            transaction_type='deposit',
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            payment=payment,
            description=f"Dépôt wallet via {payment.payments_method}",
            status='completed'
        )
        
        # Update driver balance
        driver.wallet_money = balance_after
        driver.save()
        
        # Update payment status
        payment.payments_status = 'completed'
        payment.save()
        
        logger.info(f"Deposit processed: Driver {driver.id}, Amount {amount} FCFA")
    
    @staticmethod
    def get_balance(driver):
        """Get current wallet balance for a driver."""
        return driver.wallet_money
    
    @staticmethod
    def get_transaction_history(driver, limit=50):
        """
        Get wallet transaction history for a driver.
        
        Args:
            driver: Drivers instance
            limit: Number of transactions to return
            
        Returns:
            QuerySet: WalletTransaction objects
        """
        return WalletTransaction.objects.filter(
            driver=driver
        ).select_related('ride', 'payment')[:limit]
```

**Steps:**
- [ ] Create `payments/services/` directory
- [ ] Create `__init__.py` in services directory
- [ ] Create `wallet_service.py` with above code
- [ ] Test imports work correctly

---

#### Task 3.2: Update Ride Completion to Use WalletService ⏱️ 30 min
**File:** `rides/views.py` - function `driver_complete_rides()`

**Changes:**
```python
# Add imports at top
from django.db import transaction
from payments.services.wallet_service import WalletService
import logging

logger = logging.getLogger(__name__)

# Update function (around line 628)
@api_view(['GET'])
def driver_complete_rides(request, rides_id, *args, **kwargs):
    _, driver_decode = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    
    try:
        rides = Rides.objects.get(id=rides_id)
    except Rides.DoesNotExist:
        return Response({"Message": "Rides Does Not Exist"}, status=404)
    
    try:
        driver = Drivers.objects.get(id=driver_decode.id)
    except Drivers.DoesNotExist:
        return Response({"Message": "Drivers Does Not Exist"}, status=404)
    
    if rides.status != 'in_progress':
        return Response(
            {"Message": "La course n'est pas en cours"},
            status=400
        )
    
    # Use transaction to ensure atomicity
    try:
        with transaction.atomic():
            # 1. Update ride status
            rides.status = "completed"
            rides.end_time = timezone.now()
            rides.save()
            
            # 2. Process commission using WalletService
            result = WalletService.process_ride_commission(rides, driver)
            
            # 3. Mark driver available
            driver.is_available = True
            driver.save()
            
            # 4. Send notification to client
            Notifications.objects.create(
                sender=driver,
                recipient=rides.client_id,
                notification_type='ride_completed',
                message="Votre course est terminée. Merci d'avoir utilisé Toya!",
                event_id=rides.id
            )
            
            return Response({
                "Message": "Course terminée avec succès",
                "ride_id": str(rides.id),
                "commission_amount": float(result['commission_amount']),
                "commission_rate": f"{result['commission_rate']}%",
                "net_earning": float(result['net_earning'])
            }, status=200)
            
    except ValueError as e:
        # Wallet insufficient - keep ride in progress
        logger.error(f"Ride completion failed for {rides.id}: {str(e)}")
        return Response({
            "Message": "Impossible de terminer la course",
            "error": "insufficient_wallet",
            "details": str(e),
            "action_required": "Veuillez recharger votre wallet avant de terminer la course."
        }, status=400)
    
    except Exception as e:
        logger.error(f"Unexpected error completing ride {rides.id}: {str(e)}")
        return Response({
            "Message": "Erreur lors de la terminaison de la course",
            "error": str(e)
        }, status=500)
```

**Testing:**
- [ ] Test ride completion with sufficient wallet
- [ ] Test ride completion with insufficient wallet
- [ ] Verify ride stays in_progress on payment failure
- [ ] Verify WalletTransaction records created
- [ ] Verify balance updated correctly

---

### **PHASE 4: Update Deposit Flow (30 min)**

#### Task 4.1: Integrate WalletService into Payment Success Handler ⏱️ 30 min
**File:** `payments/payment.py` - class `PaymentProcess`

**Find the launch_process method and update:**
```python
def launch_process(self, status, transaction_id):
    """Process payment status updates from S3 Mobile Pay"""
    from payments.services.wallet_service import WalletService
    import logging
    
    logger = logging.getLogger(__name__)
    
    if status == 'SUCCESS':
        try:
            # Use WalletService to process deposit
            WalletService.process_deposit_success(transaction_id)
            logger.info(f"Deposit successful: {transaction_id}")
            
            # Send success notification (existing code)
            # ...
            
        except Exception as e:
            logger.error(f"Failed to process deposit {transaction_id}: {e}")
    
    elif status == 'PENDING':
        # Existing pending logic
        pass
    
    elif status == 'FAILED':
        # Existing failed logic
        pass
```

**Testing:**
- [ ] Test deposit flow end-to-end
- [ ] Verify WalletTransaction created on success
- [ ] Verify balance updated correctly
- [ ] Test with failed payment

---

### **PHASE 5: Testing & Validation (30 min)**

#### Task 5.1: End-to-End Testing ⏱️ 30 min

**Test Scenarios:**

1. **Ride Acceptance:**
   - [ ] Driver with Bronze grade (20%) accepts 5000 FCFA ride
   - [ ] System requires 1000 FCFA in wallet
   - [ ] Driver with Gold grade (18%) accepts same ride
   - [ ] System requires 900 FCFA in wallet
   - [ ] Driver with insufficient balance gets proper error

2. **Wallet Deposit:**
   - [ ] Driver deposits 10000 FCFA via Orange Money
   - [ ] WalletTransaction record created
   - [ ] Balance updated correctly
   - [ ] Can view transaction in history

3. **Ride Completion:**
   - [ ] Complete ride with sufficient wallet
   - [ ] Commission deducted based on grade
   - [ ] WalletTransaction records created
   - [ ] Balance updated correctly
   - [ ] Notifications sent

4. **Ride Completion Failure:**
   - [ ] Try to complete ride with insufficient wallet
   - [ ] Ride stays in 'in_progress' status
   - [ ] No balance change
   - [ ] Proper error message returned

5. **Transaction History:**
   - [ ] View wallet transactions
   - [ ] Verify all transactions recorded
   - [ ] Verify balance calculations correct

---

## 📊 **Success Criteria**

- [x] Ride acceptance uses grade-based commission (not hardcoded)
- [x] All wallet operations create WalletTransaction records
- [x] Commission deduction is atomic (all or nothing)
- [x] Proper error handling for insufficient balance
- [x] Wallet balance uses Decimal (not Integer)
- [x] Grade commission rate used throughout system
- [x] No breaking changes to existing API contracts

---

## 🚫 **Out of Scope (Defer)**

These items are intentionally NOT included in this implementation:
- GPS-based ride completion validation
- Client-side ride completion
- Ride cancellation endpoints
- Advanced transaction history filtering
- Wallet withdrawal functionality
- Balance reconciliation tools
- Admin wallet adjustment endpoints

**Reason:** Focus on core wallet functionality. These can be added later without refactoring.

---

## 📝 **Notes for Future**

### Potential Enhancements:
1. **Async Payment Processing:** Move commission deduction to Celery task
2. **Balance Reconciliation:** Tool to verify balance matches transaction history
3. **Transaction Rollback:** Ability to reverse transactions
4. **Wallet Limits:** Min/max balance constraints
5. **Transaction Fees:** Additional fees for certain operations
6. **Multi-currency:** Support for different currencies

### Technical Debt:
- `PaymentsDrivers` model still used for backward compatibility
- Consider consolidating into WalletTransaction only
- Notification system could be more robust
- Add more comprehensive logging

---

## 🆘 **Troubleshooting**

### Common Issues:

**Issue:** Migration fails for wallet_money field change
**Solution:** Django should auto-convert IntegerField to DecimalField. If issues, create custom migration.

**Issue:** Circular import errors
**Solution:** Import models inside functions, not at module level

**Issue:** Transaction rollback not working
**Solution:** Ensure all operations inside `transaction.atomic()` block

**Issue:** Balance mismatch
**Solution:** Check all WalletTransaction records, sum amounts, compare to current balance

---

## ✅ **Completion Checklist**

Before marking this task complete:
- [ ] All 5 phases completed
- [ ] All tests passing
- [ ] No breaking changes to existing APIs
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Deployed to dev environment
- [ ] Manual testing completed
- [ ] Founders notified of completion

---

**Last Updated:** 2026-01-08  
**Status:** Ready for Implementation  
**Estimated Completion:** 3-4 hours
