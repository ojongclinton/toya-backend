from django.db import models
from uuid import uuid4
from core.models import BaseUser
import random 
import string


def vehicule_directory_path(instance , filename):
    
    return f"user/clients/{str(instance.id)}/{filename}" 


class Clients(BaseUser): 
    username = models.CharField(max_length=255, null=False)
    first_name = models.CharField(max_length=255, null=False)
    last_name = models.CharField(max_length=255, null=False)
    phone_number = models.CharField(max_length=15, null=False , unique=True)
    adresse = models.CharField(max_length=255, null=True)
    referral_code  = models.CharField(max_length=20, null=True , unique=True , default=None)
    profile_picture = models.ImageField(upload_to=vehicule_directory_path, null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False, help_text="Whether the user's phone number has been verified via OTP") 
    
    def save(self, *args, **kwargs) : 
        if not self.referral_code : 
            self.referral_code = self.genereate_unique_referral_code()
        super(Clients , self).save(*args, **kwargs)
        
    def genereate_unique_referral_code(self): 
        while True : 
            name = self.first_name.replace(' ', '_')
            reste = 16 - len(name)
            code = f'{name}'.upper()  + ''.join(random.choices(string.ascii_uppercase + string.digits, k=reste))
            if not Clients.objects.filter(referral_code=code).exists() : 
                return code 
        
    
    def __str__(self):
        return str(self.id)
    
    
    

