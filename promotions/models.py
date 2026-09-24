from django.db import models
from uuid import uuid4


class Promotions(models.Model) : 
    STATUS          = [ 
                       ("not_started", "Not_started"), 
                       ("active", "Active"), 
                      ("expired", "Expired"), 
                       
                       ]
    id                      = models.UUIDField(primary_key =True , unique=True , default=uuid4)
    code                    = models.CharField(max_length= 255 , unique=True)
    description             = models.TextField(null=False, default=' ')
    discount_percentage     = models.IntegerField(default=30)
    start_date              = models.DateTimeField()
    end_date                = models.DateTimeField()
    status                  = models.CharField(max_length=255 , choices=STATUS  ,default='active')
    usage_limit             = models.IntegerField(default=100)


    def __str__(self) : 
        return str(self.id)
    
    
class ApplyPromotions(models.Model) : 
    id                      = models.UUIDField(primary_key =True , unique=True , default=uuid4) 
    client_id               = models.ForeignKey('clients.clients',on_delete=models.CASCADE) 
    promotions_id           = models.ForeignKey(Promotions,on_delete=models.CASCADE) 
    applied_at              = models.DateTimeField(auto_now_add=True) 
    
    
    def __str__(self) : 
        return str(self.id)