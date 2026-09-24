from django.db import models
from uuid import uuid4
from rides.models import Rides
from core.models import BaseUser

# Create your models here.


class Conversation(models.Model):
    
    id              = models.UUIDField(primary_key=True, unique=True , default=uuid4)
    sender_id       = models.ForeignKey(BaseUser,  on_delete=models.CASCADE , related_name="sender_conversation")
    receiver_id     = models.ForeignKey(BaseUser, on_delete=models.CASCADE, related_name="reciever_conversation")       
    rides_id        = models.ForeignKey(Rides , on_delete=models.CASCADE)
    message         = models.TextField()
    timestamp       = models.DateTimeField(auto_now_add=True)
    is_read         = models.BooleanField(default=False)
    
    

    def __str__(self) : 
        return str(self.id)