import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from core.utils.translations import get_message
from core.utils.language import get_user_language


class ChatConsumer(WebsocketConsumer):
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
            rides_id = text_data_json.get("rides_id")
            
            

            if not all([message, sender_id, receiver_id, rides_id]):
                print(f"Message: {message}, Sender ID: {sender_id}, Receiver ID: {receiver_id}, Rides ID: {rides_id}")

                self.send(text_data=json.dumps({
                    "error": "Missing required fields (message, sender_id, receiver_id, or rides_id)"
                }))
                return

            conversation_data = {
                "sender_id": sender_id,
                "receiver_id": receiver_id, 
                "rides_id": rides_id,
                "message": message
            }
            
            from .serializers import ConversationSerializer
            from notifications.models import Notifications
            from core.models import BaseUser 
            
            serializer = ConversationSerializer(data=conversation_data)
            

            if serializer.is_valid():
                serializer.save()  
                
                from core.utils.notifications import send_notification_with_push
                from core.models import BaseUser
                
                try:
                    sender = BaseUser.objects.get(id=sender_id)
                    receiver = BaseUser.objects.get(id=receiver_id)
                    
                    send_notification_with_push(
                        sender=sender,
                        recipient=receiver,
                        notification_type='new_message',
                        message_key='new_message_received',
                        event_id=rides_id
                    )
                except BaseUser.DoesNotExist:
                    pass
                
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        "type": "chat.message",
                        "message": message,
                        "sender_id": sender_id,
                        "receiver_id": receiver_id,
                        "rides_id": rides_id
                    }
                )
                
                
                notification = Notifications.objects.create(
                        sender=BaseUser.objects.get(id = sender_id),
                        recipient=BaseUser.objects.get(id = receiver_id),
                        notification_type="message_received",
                        message=get_message("message_received", get_user_language, message=message),
                        event_id=rides_id
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
        rides_id = event["rides_id"]

        self.send(text_data=json.dumps({
            "message": message,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "rides_id": rides_id
        } , ensure_ascii=False))
