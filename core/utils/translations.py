# utils/translations.py

MESSAGES = {
    # ========== RIDES ==========
    'ride_requested': {
        'fr': 'Votre demande de course a été envoyée.',
        'en': 'Your ride request has been sent.'
    },
    'ride_accepted': {
        'fr': 'Votre demande de course a été acceptée par le chauffeur. Le chauffeur est en route vers votre position.',
        'en': 'Your ride request has been accepted by the driver. The driver is on the way to your pickup location.'
    },
    'ride_started': {
        'fr': 'Votre course a commencé. Profitez bien de votre trajet !',
        'en': 'Your ride has started. Sit back and enjoy your trip!'
    },
    'ride_completed': {
        'fr': 'Votre course est terminée. Merci d\'avoir utilisé Toya!',
        'en': 'Your ride is completed. Thank you for using Toya!'
    },
    'ride_canceled_by_driver': {
        'fr': 'Le chauffeur a annulé la course. Votre demande est de nouveau disponible pour d\'autres chauffeurs.',
        'en': 'The driver has cancelled the ride. Your request is now available for other drivers.'
    },
    'ride_canceled_by_client': {
        'fr': 'Le client a annulé la course.',
        'en': 'The client has cancelled the ride.'
    },
    'driver_nearby': {
        'fr': 'Le chauffeur est à proximité et arrivera bientôt. Préparez-vous.',
        'en': 'The driver is nearby and will reach your location shortly. Please get ready.'
    },
    'driver_almost_arrived': {
        'fr': 'Le chauffeur est presque arrivé. Veuillez vous préparer pour la prise en charge.',
        'en': 'The driver has almost arrived. Please prepare for pickup.'
    },
    
    # ========== WALLET & COMMISSION ==========
    'commission_refunded': {
        'fr': 'Votre commission de {amount} FCFA a été remboursée.',
        'en': 'Your commission of {amount} FCFA has been refunded.'
    },
    'commission_deducted': {
        'fr': 'Commission de {amount} FCFA ({rate}%) déduite pour la course récente.',
        'en': 'Commission of {amount} FCFA ({rate}%) deducted for recent ride.'
    },
    'insufficient_wallet': {
        'fr': 'Solde wallet insuffisant. Vous avez besoin de {amount} FCFA ({rate}% commission - Grade {grade}) pour accepter cette course.',
        'en': 'Insufficient wallet balance. You need {amount} FCFA ({rate}% commission - Grade {grade}) to accept this ride.'
    },
    
    # ========== REVIEWS ==========
    'new_review': {
        'fr': 'Vous avez reçu une nouvelle évaluation.',
        'en': 'You have received a new review with a rating.'
    },
    
    # ========== SUBSCRIPTION ==========
    'subscription_activated': {
        'fr': 'Votre abonnement a été activé avec succès. Merci pour votre paiement !',
        'en': 'Your subscription has been successfully activated. Thank you for your payment!'
    },
    
    # ========== VEHICLE ==========
    'vehicle_submitted': {
        'fr': 'Votre véhicule a été soumis pour vérification. Vous serez informé une fois le processus terminé.',
        'en': 'Your vehicle has been submitted for verification. You will be informed once the process is complete.'
    },
    'vehicle_submitted_admin': {
        'fr': 'Un chauffeur a soumis son véhicule pour inspection. Veuillez examiner la demande.',
        'en': 'A driver has submitted his vehicle for inspection. Please review the request.'
    },
    'vehicle_not_validated': {
        'fr': 'Votre véhicule n\'a pas été validé. Veuillez contacter le support.',
        'en': 'Your vehicle has not been validated. Please contact support.'
    },
    
    # ========== SUPPORT ==========
    'support_ticket_created': {
        'fr': 'Un nouveau ticket de support a été créé. Veuillez consulter les détails du ticket pour plus d\'informations.',
        'en': 'A new support ticket has been created. Please check the ticket details for more information.'
    },
    
    # ========== MESSAGES ==========
    'message_received': {
        'fr': 'Vous avez reçu un nouveau message : {message}',
        'en': 'You have received a new message: {message}'
    },
    
    # ========== NAVIGATION ==========
    'new_ride_available': {
        'fr': 'Une nouvelle course est disponible près de votre position. Consultez l\'application pour en savoir plus et accepter la course si vous êtes disponible.',
        'en': 'A new route is available near your location. Check the app to find out more and accept the ride if you\'re available.'
    },
    'course_available': {
        'fr': 'Nouvelle course disponible à {distance}km de vous. Prix: {price} FCFA',
        'en': 'New ride available {distance}km from you. Price: {price} FCFA'
    },
    
    # ========== REFERRALS ==========
    'referral_earning': {
        'fr': 'Vous avez reçu un bonus de parrainage de {amount} FCFA dans votre portefeuille.',
        'en': 'You have received a referral bonus of {amount} in your wallet.'
    },
    'referral': {
        'fr': 'Nouveau filleul inscrit avec votre code.',
        'en': 'New referral signed up with your code.'
    },
    
    # ========== PAYMENTS ==========
    'recharge_wallet': {
        'fr': 'Votre dépôt de {amount} FCFA a été effectué avec succès. Nouveau solde: {balance} FCFA',
        'en': 'Your deposit of {amount} FCFA was successful. New balance: {balance} FCFA'
    },
    'payment_failed': {
        'fr': 'Votre dépôt a échoué. Veuillez réessayer.',
        'en': 'Your deposit failed. Please try again.'
    },
    'withdraw_wallet': {
        'fr': 'Retrait de {amount} FCFA traité avec succès.',
        'en': 'Withdrawal of {amount} FCFA processed successfully.'
    },
    
    # ========== BACKOFFICE ==========
    'documents_approved': {
        'fr': 'Vos documents ont été vérifiés et approuvés avec succès par le back office. Vous pouvez maintenant accéder à toutes les fonctionnalités de la plateforme.',
        'en': 'Your documents have been successfully verified and approved by the back office. You can now access all platform features.'
    },
    'documents_rejected': {
        'fr': 'Vos documents ont été examinés par le back office mais ont été rejetés. Veuillez vérifier votre soumission et fournir les documents corrects.',
        'en': 'Your documents have been reviewed by the back office but were rejected. Please check your submission and provide the correct documents.'
    },

    # ========== WEBSOCKET TITLES ==========
    'ride_accepted_title': {
        'fr': 'Course acceptée',
        'en': 'Ride Accepted'
    },
    'ride_canceled_title': {
        'fr': 'Course annulée',
        'en': 'Ride Cancelled'
    },
    'ride_completed_title': {
        'fr': 'Course terminée',
        'en': 'Ride Completed'
    },
    'ride_started_title': {
        'fr': 'Course démarrée',
        'en': 'Ride Started'
    },
    'driver_nearby_title': {
        'fr': 'Chauffeur proche',
        'en': 'Driver Nearby'
    },
    'new_review_title': {
        'fr': 'Nouvelle évaluation',
        'en': 'New Review'
    },
    'vehicle_submitted_title': {
        'fr': 'Véhicule soumis',
        'en': 'Vehicle Submitted'
    },
    'subscription_activated_title': {
        'fr': 'Abonnement activé',
        'en': 'Subscription Activated'
    },
    'new_ride_available_title': {
        'fr': 'Nouvelle course',
        'en': 'New Ride'
    },
    'course_available_title': {
        'fr': 'Course disponible',
        'en': 'Ride Available'
    },
}


def get_message(key, language='fr', **kwargs):
    """
    Récupère un message traduit avec interpolation de variables.
    
    Args:
        key: Clé du message
        language: 'fr' ou 'en'
        **kwargs: Variables à interpoler (ex: amount=1000, rate=20)
    
    Returns:
        Message traduit avec variables interpolées
    """
    if key not in MESSAGES:
        return key  # Retourner la clé si pas trouvé
    
    message = MESSAGES[key].get(language, MESSAGES[key]['fr'])
    
    # Interpoler les variables si présentes
    if kwargs:
        try:
            message = message.format(**kwargs)
        except KeyError:
            pass  # Si variable manquante, retourner message brut
    
    return message