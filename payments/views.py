from rest_framework import status 
from rest_framework.request import Request 
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view , permission_classes 
from drf_spectacular.utils import extend_schema 
from drivers.customs import JWT as JWT_DRIVER 
from clients.customs import JWT as JWT_CLIENTS
from .models import *
from clients.models import Clients 
from drivers.models import Drivers
from .customs import WalletPayment
from .serializer import *
from rides.models import Rides 
from notifications.models import Notifications
from notifications.custums import RetrieveBackofficeUser
from referrals.models import ReferralsDrivers
from django.shortcuts import get_object_or_404
from payments.models import WalletTransaction



# ----------------------------------------DRIVERS----------------------------------------------------------------------------


@extend_schema(
    tags=['Wallet'], 
    request=WalletDepositSeriaizer, 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
def driver_make_deposit_to_his_wallet_account(request: Request, *args, **kwargs): 
    """
    Allows a driver to deposit money to their wallet.
    Credits referral bonus to the referrer on the first recharge of the referred driver.
    
    Payment status is automatically verified in the background.
    No WebSocket or manual status check required from frontend.
    """
    _, users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))
    amount = request.data.get('amount', None)
    payment_method = request.data.get('payment_method', None)
    phone_number = request.data.get('phone_number', None)

    # Validate minimum deposit amount
    if amount is None or float(amount) < 100:
        return Response(
            data={"Message": "Minimum deposit amount is 100 FCFA"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        transaction_id = WalletPayment.make_deposit_to_his_wallet_account(payment_method, amount, users, phone_number)
        
        # Trigger background task to verify payment status automatically
        from payments.tasks import verify_payment_status_task
        verify_payment_status_task.delay(transaction_id)
        
        data = {'transaction_id': transaction_id}
        content = {
            "Message": "Deposit initiated successfully. Please complete payment on your phone. Your wallet will be updated automatically.",
            'data': data
        }
        return Response(data=content, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            data={"Message": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


 




@extend_schema(
    tags=['Wallet'],
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}, 'Data': {'type': 'object'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_get_all_retrieve_wallet_account(request: Request, *args, **kwargs):
    """
    Retrieve all wallet transactions with detailed information including:
    - Transaction sign (+/-)
    - Full timestamp with hour
    - Commission rate for deductions
    - Balance before/after each transaction
    """
    from payments.models import WalletTransaction
    
    _, users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))
    
    # Récupérer toutes les transactions wallet
    transactions = WalletTransaction.objects.filter(
            driver=users
    ).exclude(
            transaction_type='commission_refund'
    ).order_by('-created_at')
    
    driver = Drivers.objects.get(id=users.id)
    
    # Formater les transactions avec tous les détails
    transactions_data = []
    for tx in transactions:
        # Déterminer le signe (+ pour crédit, - pour débit)
        if tx.transaction_type in ['deposit', 'referral_earning', 'refund']:
            sign = '+'
        else:
            sign = '-'
        
        # Format de l'heure : "21 Apr 2026, 14:30"
        timestamp = tx.created_at.strftime('%d %b %Y, %H:%M')
        
        tx_data = {
            'id': str(tx.id),
            'transaction_type': tx.transaction_type,
            'amount': float(tx.amount),
            'sign': sign,
            'balance_before': float(tx.balance_before),
            'balance_after': float(tx.balance_after),
            'description': tx.description,
            'timestamp': timestamp,
            'created_at': tx.created_at.isoformat(),
            'status': tx.status
        }
        
        # Ajouter commission_rate si c'est une déduction
        if tx.transaction_type == 'commission_deduction' and tx.commission_rate:
            tx_data['commission_rate'] = float(tx.commission_rate)
            tx_data['commission_percentage'] = f"{float(tx.commission_rate)}%"
        
        # Ajouter grade_name si présent
        if tx.grade_name:
            tx_data['grade_name'] = tx.grade_name
        
        # Ajouter ride_id si présent
        if tx.ride_id:
            tx_data['ride_id'] = str(tx.ride_id)
        
        transactions_data.append(tx_data)
    
    content = {
        "Message": "Wallet transactions retrieved successfully",
        "Data": {
            "transactions": transactions_data,
            "current_balance": float(driver.wallet_money),
            "total_transactions": len(transactions_data)
        }
    }
    
    return Response(data=content, status=status.HTTP_200_OK)



@extend_schema(
    tags=['Wallet'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
def driver_get_details_retrieve_wallet_account(request:Request ,transaction_id:str ,  *args, **kwargs): 
    _ , users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        
        wallet_payement = PaymentsDrivers.objects.filter(id =transaction_id)
        
    except PaymentsDrivers.DoesNotExist : 
        content = {"Message":"Transaction Id Does not Exist"}
        return Response(data= content , status=status.HTTP_404_NOT_FOUND)
        
    
    serializer_data = []
    
    for wallet in wallet_payement : 
        serializer_data.append( { 
                           'id':wallet.id, 
                           "amount":wallet.amount,   
                                 
                                 })
        
    content = {"Message":"Wallets" , "Data":{"All Transactions Wallet": serializer_data}}
    return Response(data= content , status=status.HTTP_200_OK)


@extend_schema(
    tags=['Wallet'],
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}, 'status': {'type': 'string'}}}}
)
@api_view(['POST'])
def check_payment_status(request: Request, *args, **kwargs):
    """
    Manually check the status of a pending payment and update wallet if successful.
    Useful for testing without WebSocket connection.
    Accepts transaction_id as query parameter.
    """
    from payments.payments.smobilepay.cashout import S3CashOutManager
    
    _, users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))
    
    # Get transaction_id from query params
    transaction_id = request.query_params.get('transaction_id')
    
    if not transaction_id:
        return Response(
            data={
                "Message": "Missing transaction_id parameter",
                "usage": "POST /api/payments/wallet/check-status?transaction_id=<your_transaction_id>"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        transaction = PaymentsDrivers.objects.get(id=transaction_id, driver_id=users.id)
    except PaymentsDrivers.DoesNotExist:
        return Response(
            data={"Message": "Transaction not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check current status
    s3_manager = S3CashOutManager()
    status_response = s3_manager.checkTransactionStatus(transaction_id)
    
    return Response(
        data={
            "Message": "Payment status checked",
            "transaction_id": transaction_id,
            "status": status_response.get('status'),
            "details": status_response
        },
        status=status.HTTP_200_OK
    )





@extend_schema(
    tags=['Wallet'],
    request=PaymentPhoneNumberSerializer,
        responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}

)
@api_view(['GET'])
def driver_manage_payment_numbers(request: Request):
    """
    Create or retrieve payment phone numbers for a driver.
    """
    # Decode and authenticate the driver
    _, users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))
    driver = get_object_or_404(Drivers, id=users.id)

    phone_numbers = PaymentPhoneNumber.objects.filter(driver=driver)
    serializer = PaymentPhoneNumberSerializer(phone_numbers, many=True)
    return Response(
        {
            "Message": "Payment phone numbers retrieved successfully",
            "Data": {"Payment Phone Numbers": serializer.data}
        },
        status=status.HTTP_200_OK
    )




@extend_schema(
    tags=['Wallet'],
    request=PaymentPhoneNumberSerializer,
    responses={
        201: {'type': 'object', 'properties': {'Message': {'type': 'string'}, 'Data': {'type': 'object'}}},
        400: {'type': 'object', 'properties': {'errors': {'type': 'object'}}}
    }
)
@api_view(['POST'])
def add_payment_phone_number(request):
    """
    Endpoint to allow drivers to add a new payment phone number.
    """
    _, users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))
    driver = get_object_or_404(Drivers, id=users.id)

    serializer = PaymentPhoneNumberSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(driver=driver)  
        return Response(
            {"Message": "Phone number added successfully", "Data": serializer.data},
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)