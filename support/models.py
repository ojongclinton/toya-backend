from django.db import models
from uuid import uuid4
from core.models import BaseUser


    
class SupportTicket(models.Model) : 
    
    SUPPORT_TICKETS =[ 
                     ('open', 'Open'), 
                     ('in_progress', 'In_progress'), 
                     ('resolved', 'Resolved'), 
                      
                      ]
    
    TYPE_USER  = [
                ('drivers' ,'Drivers'), 
                ('client' ,'Client'),
                
               ]
    
    id                 = models.UUIDField(primary_key=True, default=uuid4, null=False, unique=True)
    users_id           = models.ForeignKey(BaseUser , on_delete=models.CASCADE , null=False)
    ride               = models.ForeignKey('rides.Rides', on_delete=models.SET_NULL, null=True, blank=True, related_name='support_tickets', help_text="The associated ride for this ticket.")
    issue_description  = models.TextField()
    status             = models.CharField(max_length=255 , choices=SUPPORT_TICKETS , default='open')
    type_user          = models.CharField(max_length=20 , default='client' , null=False)
    created_at         = models.DateTimeField(auto_now_add=True)
    

    def __str__(self) : 
        return str(self.id)
    
    

class Fag(models.Model) : 
    TYPE_USER  = [
                ('drivers' ,'Drivers'), 
                ('client' ,'Client'),
                
               ]
    id          = models.UUIDField(primary_key=True, null=False, unique=True , default=uuid4)
    question    = models.TextField()
    answers     = models.TextField()
    type_user   = models.CharField(max_length=20 , default='client' , null=False)
    created_at  = models.DateTimeField(auto_now_add=True )
    
    
    
    def __str__(self) -> str:
        return str(self.id)
    
    
    
    
class SupportsConversation(models.Model):

    id              = models.UUIDField(primary_key=True, default=uuid4, null=False, unique=True)
    ticket_id       = models.ForeignKey(SupportTicket,  on_delete=models.CASCADE)
    sender_id       = models.ForeignKey(BaseUser,  on_delete=models.CASCADE , related_name="sender_supports_conversation")
    receiver_id     = models.ForeignKey(BaseUser, on_delete=models.CASCADE, related_name="reciever_supports_conversation")  
    message         = models.TextField()
    created_at      = models.DateTimeField(auto_now_add=True)
    is_read         = models.BooleanField(default=False)
    
    def __str__(self):
        return str(self.id)
