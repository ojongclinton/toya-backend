from django.db import models
from core.models import BaseUser
# Create your models here.



class BackofficeAdmin(BaseUser) :

    username = models.CharField(max_length=255, null=False)
    first_name = models.CharField(max_length=255, null=False)
    last_name = models.CharField(max_length=255, null=False)
    phone_number = models.CharField(max_length=15, null=False, unique=True)
    profile_picture = models.ImageField(upload_to='user/backoffice/', null=True, blank=True) 

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"