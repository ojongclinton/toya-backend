import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from core.utils.translations import get_message
from core.utils.language import get_user_language



class SupportConsumer(WebsocketConsumer):
    def connect(self):
        
        
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get("message")
            sender_id = text_data_json.get("sender_id")
            receiver_id = text_data_json.get("receiver_id")
            ticket_id = text_data_json.get("ticket_id")

            if not all([message, sender_id, receiver_id, ticket_id]):
                self.send(text_data=json.dumps({
                    "error": "Missing required fields (message, sender_id, receiver_id, or ticket_id)"
                }))
                return

            conversation_data = {
                "sender_id": sender_id,
                "receiver_id": receiver_id, 
                "ticket_id": ticket_id,
                "message": message
            }

            from .serializers import SupportConversationSerializer
            from notifications.models import Notifications
            from core.models import BaseUser 
            
            
            serializer = SupportConversationSerializer(data=conversation_data)

            if serializer.is_valid():
                serializer.save()  
                
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        "type": "chat.message",
                        "message": message,
                        "sender_id": sender_id,
                        "receiver_id": receiver_id,
                        "ticket_id": ticket_id
                    }
                )
                
                
                notification = Notifications.objects.create(
                        sender=BaseUser.objects.get(id = sender_id),
                        recipient=BaseUser.objects.get(id = receiver_id),
                        notification_type="support_message_received",
                        message=get_message("message_received", get_user_language, message=message),
                        event_id=ticket_id
                    )
                notification.save()
            else:

                print(f"Serialization failed: {serializer.errors}")
                self.send(text_data=json.dumps({
                    "error": f"Serialization failed: {serializer.errors}"
                }))

        except Exception as e:
            self.send(text_data=json.dumps({
                "error": f"Error processing the message: {str(e)}"
            }))

    def chat_message(self, event):
        message = event["message"]
        sender_id = event["sender_id"]
        receiver_id = event["receiver_id"]
        ticket_id = event["ticket_id"]

        self.send(text_data=json.dumps({
            "message": message,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "ticket_id": ticket_id
        }, ensure_ascii=False))
