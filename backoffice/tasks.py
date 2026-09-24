from celery import shared_task
from django.shortcuts import get_object_or_404
from core.utils.communication import Communication
from .models import BackofficeAdmin  # Assurez-vous d'importer votre modèle

@shared_task
def email_forgot_password_task(user_id):
    # Récupérez l'objet BackofficeAdmin dans la tâche
    user_instance = get_object_or_404(BackofficeAdmin, id=user_id)
    Communication().send_email_for_otp(user=user_instance)
    return "Notifications have been sent"