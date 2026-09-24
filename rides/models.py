from django.db import models
from uuid import uuid4
from django.core.validators import MaxLengthValidator , MinLengthValidator 

class Rides(models.Model):
    STATUS_RIDES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("accepted_by_driver", "Accepted by Driver"),
    ]
    
    TYPE_OF_PRESTATION = [
                    ("economy","Economy"), 
                    
                   ("confort","confort"),
                   ("prestige", "Prestige")

    ]
    
    PAYMENT_MODE = [
        ('orange_money', 'Orange Money'),
        ('mtn_money', 'MTN Mobile Money'),
        ('cash', 'Paiement en espèces'),
    ]

    
    id                      = models.UUIDField(primary_key=True , null=False , default=uuid4)
    driver_id               = models.ForeignKey('drivers.drivers', on_delete=models.CASCADE , blank=True,  null=True)
    client_id               = models.ForeignKey('clients.clients', on_delete=models.CASCADE)
    start_location          = models.CharField(max_length=255 , null=False )
    end_location            = models.CharField(max_length=255 , null=False)
    lon_start_location      =  models.FloatField(default=0.0)
    lon_end_location        = models.FloatField(default=0.0)
    lat_start_location      =  models.FloatField(default=0.0)
    lat_end_location        =  models.FloatField(default=0.0)
    accepted_time           = models.DateTimeField(auto_now_add=True)   
    start_time              = models.DateTimeField(auto_now_add=True)
    end_time                = models.DateTimeField(auto_now_add=True)
    distance                = models.FloatField(default=0.0)
    final_price             = models.FloatField(default=0.0)
    prestation              = models.CharField(max_length=255 , choices=TYPE_OF_PRESTATION , default= 'economy',  null=False)
    status                  = models.CharField(max_length=255 , choices=STATUS_RIDES ,default= 'pending',   null=False)
    notified_500m           = models.BooleanField(default=False) 
    notified_arrived        = models.BooleanField(default=False)  
    mode_of_payments        = models.CharField(max_length=255 , choices=PAYMENT_MODE ,default= 'cash',   null=False)
   
   
    def __str__(self):
       return str(self.id)
   
   
   


class ReviewRating(models.Model):
    
    id          = models.UUIDField(default=uuid4 , primary_key=True , null=False , unique=True)
    rides_id    = models.ForeignKey(Rides, on_delete=models.CASCADE , null=False)
    client_id   = models.ForeignKey("clients.clients" ,on_delete=models.CASCADE , null=False )
    driver_id   = models.ForeignKey("drivers.drivers" ,on_delete=models.CASCADE , null=False )
    rating      = models.IntegerField(default=0,  null=False )
    comment     = models.TextField(null=True )
    create_at   = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self) : 
        return str(self.id)
    
    
    