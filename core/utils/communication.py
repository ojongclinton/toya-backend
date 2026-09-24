import random

from core.models import   PasswordResetCode
from clients.models import *
from drivers.models import *
from django.utils.timezone import now
from django.core.mail import EmailMessage
from .emails import EmailSender

class Communication:
    def __init__(self) -> None:
        pass
    
    
    def generate_otp(self , user) :
        reset_code = str(random.randint(100000, 999999))

        PasswordResetCode.objects.update_or_create(
            user=user,
            defaults={
                "reset_code": reset_code,
                "created_at": now(), 
                "is_valided" : False
            }
        )

        
        
        return reset_code


    def send_email_for_otp(self,user ) : 

        email_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your  Toya Vtc  - OTP Email</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 20px;
                }}
                .message {{
                    font-size: 16px;
                    color: #555;
                    margin-bottom: 20px;
                }}
                .otp {{
                    font-size: 22px;
                    font-weight: bold;
                    color: #007bff;
                    margin-bottom: 20px;
                    text-align: center;
                }}
                .footer {{
                    font-size: 14px;
                    color: #777;
                    text-align: center;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
    <div class="container">
        <div class="header">
            🎉 Bienvenue à Toya Vtc !
        </div>
        <div class="message">
            Hi {user.first_name } {user.last_name },
        </div>
        <div class="message">
                        Merci d'utiliser Toya Vtc, votre plateforme de confiance pour la mise en relation des conducteurs et des clients. Pour compléter votre inscription ou réinitialiser votre mot de passe, veuillez utiliser le mot de passe à usage unique (OTP) suivant.
        </div>
        <div class="otp">
            {self.generate_otp(user=user)}
        </div>
        <div class="message">
            Cet OTP est valide pendant 5 minutes et vous aidera à compléter votre inscription ou à réinitialiser votre mot de passe pour Toya Vtc . Si vous ne l'avez pas demandé, veuillez ignorer cet e-mail.Bienvenue à Toya Vtc !
        </div>
        <div class="footer">
            Cordialement, <br>
                 Toya Vtc 
        </div>
    </div>
</body>

        </html>
        """

        email = user.email
        
        
        EmailSender().send_email(receiver_email=email , subject="Réinitialiser votre mot de passe |  Toya Vtc ",body=email_content)
         



