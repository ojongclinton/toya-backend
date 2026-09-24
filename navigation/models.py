from django.db import models
from uuid import uuid4
from core.models import BaseUser

class Position(models.Model): 
    id                          = models.UUIDField(primary_key=True , unique=True,  default=uuid4 , null=False)
    user_id                     = models.OneToOneField(BaseUser,  on_delete=models.CASCADE)
    lat                         = models.FloatField(default=0.0)
    lon                         = models.FloatField(default=0.0)
    address                      = models.CharField(max_length=250 )
    timestamp                   = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return self.id
    
    
class Itineraires(models.Model): 
    STATUS= [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    
    
    id                          = models.UUIDField(primary_key=True , unique=True,  default=uuid4 , null=False)
    driver_id                   = models.ForeignKey('drivers.drivers', on_delete=models.CASCADE)
    clients_id                  = models.ForeignKey('clients.clients', on_delete=models.CASCADE)
    start_lat                   = models.FloatField(default=0.0)
    start_lon                   = models.FloatField(default=0.0)
    distance                    = models.FloatField(default=0.0)
    statut                      = models.CharField(max_length=255 , default='pending' , choices=STATUS)
    date_creation               = models.DateTimeField(auto_now_add=True)    
    start_date                  = models.DateTimeField(auto_now_add=True)
    end_date                    = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self): 
        return self.id



class NavigationHistory(models.Model) : 
    id                          = models.UUIDField(primary_key=True , unique=True,  default=uuid4 , null=False)
    driver_id                   = models.ForeignKey('drivers.drivers', on_delete=models.CASCADE)
    itinerary_id                = models.ForeignKey(Itineraires, on_delete=models.CASCADE)
    timestamp                   = models.DateTimeField(auto_now_add=True)


    def __str__(self): 
        return self.id
    
    
class PositionHistory(models.Model) : 
    id                          = models.UUIDField(primary_key=True , unique=True,  default=uuid4 , null=False)
    user_id                     = models.ForeignKey(BaseUser ,  on_delete=models.CASCADE)
    lat                         = models.FloatField(default=0.0)
    lon                         = models.FloatField(default=0.0)
    address                      = models.CharField(max_length=250 )
    timestamp                   = models.DateTimeField(auto_now_add=True)


    def __str__(self): 
        return self.id