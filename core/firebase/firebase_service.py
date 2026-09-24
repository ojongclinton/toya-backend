from fcm_django.models import FCMDevice
from core.models import BaseUser


class FirebaseService:
    """
    Service pour gérer l'enregistrement des appareils et l'envoi des notifications push via Firebase.
    """

    @staticmethod
    def send_push_notification(user, title, body):
        """
        Envoie une notification push à un utilisateur spécifique.

        Args:
            user: L'utilisateur cible.
            title: Le titre de la notification.
            body: Le corps de la notification.

        Returns:
            dict: Résultat de l'envoi.
        """
        try:
            # Récupérer le premier appareil enregistré pour cet utilisateur
            device = FCMDevice.objects.filter(user=user).first()
            if device:
                device.send_message(title=title, body=body)
                return {"success": "Notification sent successfully."}
            return {"error": "No device found for this user."}
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}

    @staticmethod
    def send_bulk_notifications(user_group, title, body):
        """
        Envoie des notifications push à un groupe d'utilisateurs.

        Args:
            user_group: Liste d'utilisateurs cible.
            title: Le titre des notifications.
            body: Le corps des notifications.

        Returns:
            dict: Résultat de l'envoi.
        """
        try:
            # Récupérer tous les appareils pour les utilisateurs spécifiés
            devices = FCMDevice.objects.filter(user__in=user_group)
            if devices.exists():
                devices.send_message(title=title, body=body)
                return {"success": "Notifications sent to multiple devices."}
            return {"error": "No devices found for this group."}
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}

    @staticmethod
    def unregister_device(token):
        """
        Supprime un appareil enregistré en utilisant le token FCM.

        Args:
            token: Le token FCM de l'appareil à désenregistrer.

        Returns:
            dict: Résultat du processus de désenregistrement.
        """
        try:
            device = FCMDevice.objects.filter(registration_id=token).first()
            if device:
                device.delete()
                return {"success": "Device unregistered successfully."}
            return {"error": "Device not found."}
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}
