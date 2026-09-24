from django.contrib.auth.models import AbstractBaseUser , PermissionsMixin 
from django.db import models 
from uuid import uuid4 


class BaseUser(AbstractBaseUser, PermissionsMixin) : 
    USER_TYPES = [ 
                 ("client", "Client"), 
                 ("drivers", "Drivers"), 
                 ("admin", "Admin")
                 ]

    
    id = models.UUIDField(primary_key=True, default=uuid4, unique=True, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    
    def __str__(self):
        return str(self.id)
    
    
    
    
class PasswordResetCode(models.Model):
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE)
    reset_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_valided = models.BooleanField(default=False)


class SignupOTP(models.Model):
    """OTP codes for signup phone number verification."""
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE, related_name='signup_otp')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    
    def __str__(self):
        return f"SignupOTP for {self.user.email}"
    
    class Meta:
        verbose_name = "Signup OTP"
        verbose_name_plural = "Signup OTPs"