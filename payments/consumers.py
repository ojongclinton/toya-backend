import json
import asyncio
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import StopConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ValidationError

class PaymentStatusConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user_id = self.scope.get('url_route', {}).get('kwargs', {}).get('user_id', None)
        transaction_id = self.scope.get('url_route', {}).get('kwargs', {}).get('transaction_id', None)

        if user_id is None or transaction_id is None:
            await self.close()
            return

        if not self.is_valid_uuid(user_id) or not self.is_valid_uuid(transaction_id):
            await self.close()
            return

        try:
            self.user_id = user_id
            self.transaction_id = transaction_id
        except ValueError:
            await self.close()
            return

        self.room_group_name = f"payment_{self.transaction_id}"
        self.last_payment_status = None  

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        asyncio.create_task(self.simulate_payment_status())

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        raise StopConsumer()

    async def receive(self, text_data):
        pass

    async def simulate_payment_status(self):
        max_time = 130  
        interval = 20   
        elapsed_time = 0  

        while elapsed_time < max_time:
            payment_status_response = await self.get_payment_status(self.transaction_id)

            status = payment_status_response.get('status', 'UNKNOWN')

            if status == 'SUCCESS':
                await self.send_message(payment_status_response)
            elif status == 'FAILED':
                await self.send_message(payment_status_response)
            elif status == 'PENDING':
                await self.send_message(payment_status_response)
            elif status == 'ERRORED':
                await self.send_message(payment_status_response)
            else:
                await self.send_message(payment_status_response)

            await asyncio.sleep(interval)
            elapsed_time += interval

        await self.send_message("Payment Status Timeout")



    async def send_message(self, message):
        """
        Fonction pour envoyer un message de type SSE via WebSocket.
        Cette fonction est appelée uniquement lorsque le statut du paiement change.
        """
        await self.send(text_data=json.dumps({
            'status': message
        }))

    @database_sync_to_async
    def get_payment_status(self, transaction_id):
        from payments.payments.smobilepay.cashout import S3CashOutManager
        
        s3CashOutManager = S3CashOutManager()
        
        status_response = s3CashOutManager.checkTransactionStatus(transactionId=transaction_id)

        if status_response:  
            return status_response
        else:  
            return {
                'status': 'UNKNOWN',
                'message': {
                    "fr": {
                        'message_fr': "Statut de paiement inconnu",
                        'solution_fr': "Veuillez contacter le support pour plus de détails"
                    },
                    "en": {
                        'message_en': "Unknown payment status",
                        'solution_en': "Please contact support for more details"
                    }
                }
            }   

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        from drivers.models import Drivers

        try:
            return Drivers.objects.get(id=user_id)
        except Drivers.DoesNotExist:
            return None

    def is_valid_uuid(self, val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False
