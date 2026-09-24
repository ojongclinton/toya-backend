# Wallet Deposit Integration Guide - Simplified (React Native Expo)

## Overview

This is the **simplified version** of the wallet deposit flow. The backend automatically verifies payment status in the background using Celery tasks. **No WebSocket connection or manual status checks required from the frontend.**

---

## How It Works

```
┌─────────────┐                          ┌─────────────┐
│   Mobile    │  1. POST /make-deposit   │   Backend   │
│     App     │ ──────────────────────>  │   (Django)  │
└─────────────┘                          └─────────────┘
       │                                        │
       │  2. Response: transaction_id          │
       │ <──────────────────────────────────── │
       │                                        │
       │                                        │ 3. Celery task starts
       │                                        │    (background polling)
       │                                        │
       │                                        ▼
       │                                  ┌──────────┐
       │                                  │ S3 API   │
       │                                  │ Polling  │
       │                                  │ (20s×6)  │
       │                                  └──────────┘
       │                                        │
       │                                        │ 4. Status = SUCCESS
       │                                        │    Wallet updated
       │                                        │
       │  5. GET /wallet/history               │
       │ ──────────────────────────────────>   │
       │                                        │
       │  6. Updated balance                   │
       │ <──────────────────────────────────── │
```

**Key Points:**
- Frontend only makes **2 HTTP calls**: deposit initiation + balance refresh
- Backend handles all verification automatically via Celery
- User can close the app after initiating deposit
- Wallet updates happen even if app is closed

---

## Prerequisites

```bash
# No special packages needed - just standard fetch API
npm install @react-native-community/netinfo  # Optional: for network status
```

---

## Implementation

### Step 1: Create Wallet Service

```javascript
// services/WalletService.js
import { API_CONFIG } from '../config/api';

class WalletService {
  /**
   * Initiate a wallet deposit
   * Backend automatically verifies payment in background
   */
  async initiateDeposit(token, amount, paymentMethod, phoneNumber) {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/payments/wallet/make-deposit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount,
          payment_method: paymentMethod,
          phone_number: phoneNumber,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.Message || 'Failed to initiate deposit');
      }

      return data.data; // { transaction_id: "..." }
    } catch (error) {
      console.error('Deposit initiation error:', error);
      throw error;
    }
  }

  /**
   * Get wallet transaction history and current balance
   */
  async getWalletHistory(token) {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/payments/wallet/history`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.Message || 'Failed to fetch history');
      }

      return data.Data;
    } catch (error) {
      console.error('Wallet history error:', error);
      throw error;
    }
  }

  /**
   * Optional: Manually check payment status
   * (Only needed if user wants to check before automatic verification completes)
   */
  async checkPaymentStatus(token, transactionId) {
    try {
      const response = await fetch(
        `${API_CONFIG.BASE_URL}/api/payments/wallet/check-status?transaction_id=${transactionId}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.Message || 'Failed to check status');
      }

      return data;
    } catch (error) {
      console.error('Status check error:', error);
      throw error;
    }
  }
}

export default new WalletService();
```

---

### Step 2: Create Wallet Deposit Screen

```javascript
// screens/WalletDepositScreen.js
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import WalletService from '../services/WalletService';

const WalletDepositScreen = ({ navigation }) => {
  const { token } = useAuth();
  const [amount, setAmount] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('orange_money');
  const [loading, setLoading] = useState(false);

  const handleDeposit = async () => {
    // Validation
    if (!amount || parseFloat(amount) < 100) {
      Alert.alert('Error', 'Minimum deposit amount is 100 FCFA');
      return;
    }

    if (!phoneNumber) {
      Alert.alert('Error', 'Please enter your phone number');
      return;
    }

    setLoading(true);

    try {
      // Initiate deposit - backend handles verification automatically
      const result = await WalletService.initiateDeposit(
        token,
        parseFloat(amount),
        paymentMethod,
        phoneNumber
      );

      setLoading(false);

      Alert.alert(
        'Payment Initiated',
        'Please check your phone for the USSD prompt and enter your PIN. Your wallet will be updated automatically within 2 minutes.',
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]
      );

    } catch (error) {
      setLoading(false);
      Alert.alert('Error', error.message);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Recharge Wallet</Text>

      <TextInput
        style={styles.input}
        placeholder="Amount (min. 100 FCFA)"
        keyboardType="numeric"
        value={amount}
        onChangeText={setAmount}
      />

      <TextInput
        style={styles.input}
        placeholder="Phone Number (+237XXXXXXXXX)"
        keyboardType="phone-pad"
        value={phoneNumber}
        onChangeText={setPhoneNumber}
      />

      <View style={styles.paymentMethodContainer}>
        <TouchableOpacity
          style={[
            styles.methodButton,
            paymentMethod === 'orange_money' && styles.methodButtonActive,
          ]}
          onPress={() => setPaymentMethod('orange_money')}
        >
          <Text style={styles.methodText}>Orange Money</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.methodButton,
            paymentMethod === 'mtn_money' && styles.methodButtonActive,
          ]}
          onPress={() => setPaymentMethod('mtn_money')}
        >
          <Text style={styles.methodText}>MTN Money</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={handleDeposit}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Deposit</Text>
        )}
      </TouchableOpacity>

      <Text style={styles.infoText}>
        💡 Your wallet will be updated automatically. You can close the app after completing the USSD payment.
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 30,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    fontSize: 16,
  },
  paymentMethodContainer: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  methodButton: {
    flex: 1,
    padding: 15,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    marginHorizontal: 5,
    alignItems: 'center',
  },
  methodButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  methodText: {
    fontSize: 14,
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  infoText: {
    marginTop: 20,
    textAlign: 'center',
    color: '#666',
    fontSize: 13,
  },
});

export default WalletDepositScreen;
```

---

### Step 3: Display Updated Balance

```javascript
// screens/WalletScreen.js
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, RefreshControl, ScrollView } from 'react-native';
import { useAuth } from '../context/AuthContext';
import WalletService from '../services/WalletService';

const WalletScreen = () => {
  const { token } = useAuth();
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadWalletData = async () => {
    try {
      const data = await WalletService.getWalletHistory(token);
      setBalance(data['All Gain']);
      setTransactions(data['All Transactions Wallet']);
    } catch (error) {
      console.error('Error loading wallet:', error);
    }
  };

  useEffect(() => {
    loadWalletData();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadWalletData();
    setRefreshing(false);
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.balanceCard}>
        <Text style={styles.balanceLabel}>Current Balance</Text>
        <Text style={styles.balanceAmount}>{balance} FCFA</Text>
      </View>

      <Text style={styles.sectionTitle}>Recent Transactions</Text>
      {transactions.map((tx) => (
        <View key={tx.id} style={styles.transactionItem}>
          <Text>{tx.payment_type}</Text>
          <Text>{tx.amount} FCFA</Text>
        </View>
      ))}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  balanceCard: {
    backgroundColor: '#007AFF',
    padding: 30,
    margin: 20,
    borderRadius: 12,
    alignItems: 'center',
  },
  balanceLabel: {
    color: '#fff',
    fontSize: 16,
    marginBottom: 10,
  },
  balanceAmount: {
    color: '#fff',
    fontSize: 36,
    fontWeight: 'bold',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginHorizontal: 20,
    marginBottom: 10,
  },
  transactionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 15,
    marginHorizontal: 20,
    marginBottom: 10,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
});

export default WalletScreen;
```

---

## User Flow

1. **User initiates deposit**
   - Enters amount, phone number, selects payment method
   - Taps "Deposit" button

2. **App calls backend**
   - `POST /api/payments/wallet/make-deposit`
   - Receives `transaction_id`
   - Shows success message

3. **User completes USSD payment**
   - Receives USSD prompt on phone
   - Enters PIN
   - **Can close the app** - verification continues in background

4. **Backend verifies automatically** (no frontend action needed)
   - Celery task polls S3 API every 20 seconds
   - When payment succeeds, wallet is updated
   - Takes up to 2 minutes

5. **User checks balance later**
   - Opens wallet screen
   - Pulls to refresh
   - Sees updated balance

---

## Advantages of This Approach

✅ **No WebSocket complexity** - Simple HTTP REST calls only  
✅ **Works when app is closed** - Backend handles everything  
✅ **No connection management** - No need to handle disconnects  
✅ **Better UX** - User doesn't need to wait in app  
✅ **More reliable** - Celery ensures task completion  
✅ **Simpler code** - ~50% less frontend code  

---

## Optional: Manual Status Check

If the user wants to check status immediately (before automatic verification completes):

```javascript
const checkStatus = async (transactionId) => {
  try {
    const result = await WalletService.checkPaymentStatus(token, transactionId);
    
    if (result.status === 'SUCCESS') {
      Alert.alert('Success', 'Payment completed! Your wallet has been updated.');
      // Refresh wallet balance
      loadWalletData();
    } else if (result.status === 'PENDING') {
      Alert.alert('Pending', 'Payment is still being processed. Please wait...');
    } else {
      Alert.alert('Failed', 'Payment failed. Please try again.');
    }
  } catch (error) {
    console.error('Status check error:', error);
  }
};
```

---

## Backend Requirements

**Ensure Celery is running:**

```bash
# Start Celery worker
celery -A core worker --loglevel=info

# For development (with auto-reload)
watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A core worker --loglevel=info
```

**Docker Compose (if using):**
```yaml
services:
  celery:
    build: .
    command: celery -A core worker --loglevel=info
    depends_on:
      - redis
      - db
```

---

## Testing

### Test Checklist

- [ ] Initiate deposit with amount >= 100 FCFA
- [ ] Complete USSD payment on phone
- [ ] Close app after USSD prompt
- [ ] Wait 2 minutes
- [ ] Open app and check wallet balance
- [ ] Verify balance is updated

### Monitoring Logs

```bash
# Check Celery task execution
docker-compose logs -f celery | grep "verify_payment_status_task"

# Expected logs:
# Starting background verification for transaction abc-123...
# Checking payment status (attempt 1/6)...
# Transaction abc-123 status: PENDING
# Checking payment status (attempt 2/6)...
# Transaction abc-123 status: SUCCESS
# Payment successful. Wallet updated.
```

---

## API Reference

### POST /api/payments/wallet/make-deposit

**Request:**
```json
{
  "amount": 500,
  "payment_method": "orange_money",
  "phone_number": "+237XXXXXXXXX"
}
```

**Response:**
```json
{
  "Message": "Deposit initiated successfully. Please complete payment on your phone. Your wallet will be updated automatically.",
  "data": {
    "transaction_id": "abc-123-def-456"
  }
}
```

### GET /api/payments/wallet/history

**Response:**
```json
{
  "Message": "Wallets retrieved successfully",
  "Data": {
    "All Transactions Wallet": [
      {
        "id": "abc-123",
        "amount": 500.00,
        "payment_type": "wallet_pay"
      }
    ],
    "All Gain": 5000.00
  }
}
```

### POST /api/payments/wallet/check-status?transaction_id={id}

**Response:**
```json
{
  "Message": "Payment status checked",
  "transaction_id": "abc-123",
  "status": "SUCCESS",
  "details": { ... }
}
```

---

## Summary

**Frontend needs to do:**
1. Call deposit endpoint
2. Show USSD instruction to user
3. Refresh wallet balance when user returns to app

**Backend handles automatically:**
1. Poll S3 Mobile Pay API every 20 seconds
2. Update wallet when payment succeeds
3. Log all status changes

**Result:** Much simpler frontend implementation with better reliability!
