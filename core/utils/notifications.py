# utils/notifications.py

from notifications.models import Notifications
from .translations import get_message
from .language import get_user_language
from core.firebase.firebase_service import FirebaseService


def send_notification_with_push(sender, recipient, notification_type, message_key, event_id=None, **kwargs):
    """
    Envoie notification complète : DB + Push Firebase
    
    Args:
        sender: User qui envoie
        recipient: User qui reçoit  
        notification_type: Type de notification ('ride_accepted', etc.)
        message_key: Clé dans translations.py ('ride_accepted', etc.)
        event_id: ID de l'événement lié (ride, etc.)
        **kwargs: Variables pour interpolation (amount=1000, rate=20, etc.)
    
    Returns:
        Notification object created
        
    Example:
        send_notification_with_push(
            sender=driver,
            recipient=client,
            notification_type='ride_accepted',
            message_key='ride_accepted',
            event_id=ride.id
        )
    """
    
    # 1. Récupérer la langue du destinataire
    user_language = get_user_language(user=recipient)
    
    # 2. Traduire le message et le titre
    message_body = get_message(message_key, user_language, **kwargs)
    message_title = get_message(f"{message_key}_title", user_language, **kwargs)
    
    # 3. Créer notification en base de données
    notification = Notifications.objects.create(
        sender=sender,
        recipient=recipient,
        notification_type=notification_type,
        message=message_body,
        event_id=event_id
    )
    
    # 4. Envoyer Push Firebase
    try:
        result = FirebaseService.send_push_notification(
            user=recipient,
            title=message_title,
            body=message_body
        )
        
        # Logger le résultat (optionnel)
        if "error" in result:
            print(f"⚠️  Push notification warning for {recipient}: {result['error']}")
        else:
            print(f"✅ Push notification sent to {recipient}")
            
    except Exception as e:
        # Ne pas bloquer si Firebase échoue
        print(f"❌ Push notification failed for {recipient}: {e}")
    
    return notification


def send_notification_to_group(sender, recipients, notification_type, message_key, event_id=None, **kwargs):
    """
    Envoie notifications à un groupe d'utilisateurs
    
    Args:
        sender: User qui envoie
        recipients: Liste de users qui reçoivent
        notification_type: Type de notification
        message_key: Clé dans translations.py
        event_id: ID de l'événement lié
        **kwargs: Variables pour interpolation
    
    Returns:
        Liste des notifications créées
    """
    
    notifications = []
    
    for recipient in recipients:
        notif = send_notification_with_push(
            sender=sender,
            recipient=recipient,
            notification_type=notification_type,
            message_key=message_key,
            event_id=event_id,
            **kwargs
        )
        notifications.append(notif)
    
    return notifications
