


ERROR_CODES = {
    0: {
        "en": ("Transaction processing did not trigger an error", "It’s either still being processed or was already successfully processed. No error. Check the payment status."),
        "fr": ("Le traitement de la transaction n'a pas déclenché d'erreur", "Elle est soit encore en cours de traitement, soit déjà traitée avec succès. Aucune erreur. Vérifiez le statut du paiement.")
    },
    2: {
        "en": ("Transaction is under investigation", "Contact support for details."),
        "fr": ("La transaction est en cours d'investigation", "Contactez le support pour plus de détails.")
    },
    3: {
        "en": ("Transaction has been reversed", "Contact support for details."),
        "fr": ("La transaction a été annulée", "Contactez le support pour plus de détails.")
    },
    40401: {
        "en": ("No free vouchers available", "No free vouchers available."),
        "fr": ("Aucun bon gratuit disponible", "Aucun bon gratuit disponible.")
    },
    40701: {
        "en": ("Payment ran into timeout during execution", "Re-request a new quote and retry."),
        "fr": ("Le paiement a rencontré un délai d'attente lors de l'exécution", "Demandez un nouveau devis et réessayez.")
    },
    41002: {
        "en": ("Gateway balance insufficient", "Try again later. Contact support if issue persists."),
        "fr": ("Solde de la passerelle insuffisant", "Réessayez plus tard. Contactez le support si le problème persiste.")
    },
    41004: {
        "en": ("Gateway to service provider temporarily unavailable", "Try again later."),
        "fr": ("Passerelle vers le fournisseur de services temporairement indisponible", "Réessayez plus tard.")
    },
    60001: {
        "en": ("No open agent session", "Contact support for details."),
        "fr": ("Aucune session d'agent ouverte", "Contactez le support pour plus de détails.")
    },
    60003: {
        "en": ("Company session is not open", "Contact support for details."),
        "fr": ("La session de l'entreprise n'est pas ouverte", "Contactez le support pour plus de détails.")
    },
    60010: {
        "en": ("Invalid drawer assignment", "Contact support for details."),
        "fr": ("Attribution de tiroir invalide", "Contactez le support pour plus de détails.")
    },
    702000: {
        "en": ("Transaction failed due to a general payment error", "Contact support for details."),
        "fr": ("Échec de la transaction en raison d'une erreur de paiement générale", "Contactez le support pour plus de détails.")
    },
    702100: {
        "en": ("Transaction failed when initializing communications with the service provider", "Contact support if this error persists during retry."),
        "fr": ("Échec de la transaction lors de l'initialisation des communications avec le fournisseur de services", "Contactez le support si cette erreur persiste lors de la nouvelle tentative.")
    },
    702101: {
        "en": ("Destination does not match expected value range", "Correct error in request and retry. Please validate input against configuration details of service."),
        "fr": ("La destination ne correspond pas à la plage de valeurs attendues", "Corrigez l'erreur dans la demande et réessayez. Veuillez valider les données d'entrée en fonction des détails de la configuration du service.")
    },
    702102: {
        "en": ("The transaction was rejected because the amount is below the acceptable threshold", "Correct error in request and retry. Please validate input against configuration details of service."),
        "fr": ("La transaction a été rejetée car le montant est inférieur au seuil acceptable", "Corrigez l'erreur dans la demande et réessayez. Veuillez valider les données d'entrée en fonction des détails de la configuration du service.")
    },
    702103: {
        "en": ("The transaction was rejected because the amount is above the acceptable threshold", "Correct error in request and retry. Please validate input against configuration details of service."),
        "fr": ("La transaction a été rejetée car le montant dépasse le seuil acceptable", "Corrigez l'erreur dans la demande et réessayez. Veuillez valider les données d'entrée en fonction des détails de la configuration du service.")
    },
    702105: {
        "en": ("The transaction timeout at the level of Service Provider", "Check the payment status. It has to be moved to a clear ERROR or SUCCESS and act accordingly."),
        "fr": ("Le délai d'attente de la transaction au niveau du fournisseur de services", "Vérifiez le statut du paiement. Il doit être déplacé vers une erreur claire ou un succès et agissez en conséquence.")
    },
    702106: {
        "en": ("Transaction failed. The Service Provider could not be reached temporarily", "Try again later. Contact support if issue persists."),
        "fr": ("La transaction a échoué. Le fournisseur de services n'a pas pu être atteint temporairement", "Réessayez plus tard. Contactez le support si le problème persiste.")
    },

703000: {
        "en": ("Transaction failed due to a general business error", "Contact support for details."),
        "fr": ("Échec de la transaction en raison d'une erreur générale commerciale", "Contactez le support pour plus de détails.")
    },
    703020: {
        "en": ("The Service Provider could not be reached temporarily (after transaction initialization phase)", "Try again later. Contact support if issue persists."),
        "fr": ("Le fournisseur de services n'a pas pu être atteint temporairement (après la phase d'initialisation de la transaction)", "Réessayez plus tard. Contactez le support si le problème persiste.")
    },
    703100: {
        "en": ("Invalid input in request - one or more fields of the payment input request are invalid and were rejected", "Correct error in request and retry. Please validate input against configuration details of service."),
        "fr": ("Entrée invalide dans la demande - un ou plusieurs champs de la demande de paiement sont invalides et ont été rejetés", "Corrigez l'erreur dans la demande et réessayez. Veuillez valider les données d'entrée en fonction des détails de la configuration du service.")
    },
    703102: {
        "en": ("Service Provider has rejected the transaction", "Try again. Contact support for details if issue persists."),
        "fr": ("Le fournisseur de services a rejeté la transaction", "Réessayez. Contactez le support pour plus de détails si le problème persiste.")
    },
    703103: {
        "en": ("Recipient account with Service Provider is blocked", "Inform customer."),
        "fr": ("Le compte du destinataire auprès du fournisseur de services est bloqué", "Informez le client.")
    },
    703104: {
        "en": ("Sender account with Service Provider is blocked", "Inform customer."),
        "fr": ("Le compte de l'expéditeur auprès du fournisseur de services est bloqué", "Informez le client.")
    },
    703105: {
        "en": ("Service Provider does not know the recipient (account) of the transaction", "Inform customer."),
        "fr": ("Le fournisseur de services ne connaît pas le destinataire (compte) de la transaction", "Informez le client.")
    },
    703106: {
        "en": ("Service provider does not know the Sender/Initiator Account of the transaction", "Inform customer."),
        "fr": ("Le fournisseur de services ne connaît pas le compte de l'expéditeur/initiateur de la transaction", "Informez le client.")
    },
    703107: {
        "en": ("Recipient Account does not have sufficient funds with the Service Provider to perform this transaction.", "Inform customer."),
        "fr": ("Le compte du destinataire n'a pas suffisamment de fonds auprès du fournisseur de services pour effectuer cette transaction.", "Informez le client.")
    },
    703108: {
        "en": ("Initiator (sender) Account does not have sufficient funds with the Service Provider to perform this transaction", "Inform customer."),
        "fr": ("Le compte de l'initiateur (expéditeur) n'a pas suffisamment de fonds auprès du fournisseur de services pour effectuer cette transaction", "Informez le client.")
    },
    703109: {
        "en": ("Service Provider rejected the transaction because the amount is below the threshold allowed", "Correct error in request and retry. Please validate input against configuration details of service."),
        "fr": ("Le fournisseur de services a rejeté la transaction car le montant est inférieur au seuil autorisé", "Corrigez l'erreur dans la demande et réessayez. Veuillez valider les données d'entrée en fonction des détails de la configuration du service.")
    },
    703110: {
        "en": ("Service Provider rejected the transaction because the amount is above the threshold allowed", "Correct error in request and retry. Please validate input against configuration details of service."),
        "fr": ("Le fournisseur de services a rejeté la transaction car le montant dépasse le seuil autorisé", "Corrigez l'erreur dans la demande et réessayez. Veuillez valider les données d'entrée en fonction des détails de la configuration du service.")
    },
    703111: {
        "en": ("Sender/Initiator account has exceeded the limit (daily, weekly, monthly etc) with the Service Provider", "Inform customer."),
        "fr": ("Le compte de l'expéditeur/initiateur a dépassé la limite (quotidienne, hebdomadaire, mensuelle, etc.) auprès du fournisseur de services", "Informez le client.")
    },
    703112: {
        "en": ("Recipient account has exceeded the limit (daily, weekly, monthly etc) with the Service Provider", "Inform customer."),
        "fr": ("Le compte du destinataire a dépassé la limite (quotidienne, hebdomadaire, mensuelle, etc.) auprès du fournisseur de services", "Informez le client.")
    },
    703113: {
        "en": ("Payment Item (e.g. for bill payments) is no longer available for payment or has already been paid", "Retrieve currently available payment item id based on service type."),
        "fr": ("L'élément de paiement (par exemple, pour les paiements de factures) n'est plus disponible pour le paiement ou a déjà été payé", "Récupérez l'identifiant de l'élément de paiement actuellement disponible en fonction du type de service.")
    },
    703114: {
        "en": ("The Service Provider has rejected the transaction amount. Invalid Amount in the transaction", "Correct error in request and retry. Please validate input against configuration details of service."),
        "fr": ("Le fournisseur de services a rejeté le montant de la transaction. Montant invalide dans la transaction", "Corrigez l'erreur dans la demande et réessayez. Veuillez valider les données d'entrée en fonction des détails de la configuration du service.")
    },
    703117: {
        "en": ("The Service Provider does not support the Account number in the transaction.", "Inform customer."),
        "fr": ("Le fournisseur de services ne prend pas en charge le numéro de compte dans la transaction.", "Informez le client.")
    },
    703201: {
        "en": ("Payment requires a customer confirmation to complete. Confirmation has not been given by customer.", "Inform customer."),
        "fr": ("Le paiement nécessite une confirmation du client pour être complété. La confirmation n'a pas été donnée par le client.", "Informez le client.")
    },
    703202: {
        "en": ("Customer has rejected the payment / denied the approval of the transaction. The transaction cannot complete without the customer confirmation.", "Inform customer. Retry payment."),
        "fr": ("Le client a rejeté le paiement / refusé l'approbation de la transaction. La transaction ne peut pas être complétée sans la confirmation du client.", "Informez le client. Réessayez le paiement.")
    },
    703203: {
        "en": ("Customer has provided Wrong/Invalid approval credentials which resulted in a rejection of the transaction by the Service Provider (e.g. wrong/invalid PIN, expired OTP, etc.). The transaction cannot complete without the customer confirmation.", "Inform customer. Retry payment."),
        "fr": ("Le client a fourni des informations d'approbation erronées/invalides, ce qui a entraîné un rejet de la transaction par le fournisseur de services (par exemple, PIN incorrect, OTP expiré, etc.). La transaction ne peut pas être complétée sans la confirmation du client.", "Informez le client. Réessayez le paiement.")
    },
    703401: {
        "en": ("Error indicating that the connector could not find the transaction in the Service Provider System when performing a status check.", "Contact support for details."),
        "fr": ("Erreur indiquant que le connecteur n'a pas trouvé la transaction dans le système du fournisseur de services lors de la vérification du statut.", "Contactez le support pour plus de détails.")
    },
    703501: {
        "en": ("Technical error during validation of payment with service provider", "Contact support for details."),
        "fr": ("Erreur technique lors de la validation du paiement avec le fournisseur de services", "Contactez le support pour plus de détails.")
    },
    703503: {
        "en": ("Service provider system is under maintenance", "Try again. Contact support for details if issue persists."),
        "fr": ("Le système du fournisseur de services est en maintenance", "Réessayez. Contactez le support pour plus de détails si le problème persiste.")
    },
    704000: {
        "en": ("Technical error", "Contact support for details."),
        "fr": ("Erreur technique", "Contactez le support pour plus de détails.")
    },
    704003: {
        "en": ("Payment processing error", "Contact support for details."),
        "fr": ("Erreur de traitement du paiement", "Contactez le support pour plus de détails.")
    },
    704004: {
        "en": ("The time between searching for and paying for a payable item was too long and has expired.", "Please retry from start."),
        "fr": ("Le temps entre la recherche et le paiement d'un article payable était trop long et a expiré.", "Veuillez réessayer depuis le début.")
    },
    704005: {
        "en": ("Technical error during validation of payment with service provider", "Contact support for details."),
        "fr": ("Erreur technique lors de la validation du paiement avec le fournisseur de services", "Contactez le support pour plus de détails.")
    },
    704006: {
        "en": ("Unknown response provided by Service Provider", "Contact support for details."),
        "fr": ("Réponse inconnue fournie par le fournisseur de services", "Contactez le support pour plus de détails.")
    },
    705000: {
        "en": ("Unexpected technical error", "Contact support for details."),
        "fr": ("Erreur technique inattendue", "Contactez le support pour plus de détails.")
    },
    705010: {
        "en": ("Timeout during communication with service provider", "Try again later. Contact support if issue persists."),
        "fr": ("Délai d'attente lors de la communication avec le fournisseur de services", "Réessayez plus tard. Contactez le support si le problème persiste.")
    },
    705020: {
        "en": ("Timeout during communication with service provider", "Try again later. Contact support if issue persists."),
        "fr": ("Délai d'attente lors de la communication avec le fournisseur de services", "Réessayez plus tard. Contactez le support si le problème persiste.")
    },
    705030: {
        "en": ("Timeout during communication with service provider", "Try again later. Contact support if issue persists."),
        "fr": ("Délai d'attente lors de la communication avec le fournisseur de services", "Réessayez plus tard. Contactez le support si le problème persiste.")
    },
    90000: {
        "en": ("Internal server error", "Try again later. Contact support if issue persists."),
        "fr": ("Erreur interne du serveur", "Réessayez plus tard. Contactez le support si le problème persiste.")
    }, 
    90000: {
        "en": ("Internal server error", "Try again later. Contact support if issue persists."),
        "fr": ("Erreur interne du serveur", "Réessayez plus tard. Contactez le support si le problème persiste.")
    },



    "default": {
        "en": ("Unknown error occurred", "Please contact support for more details."),
        "fr": ("Une erreur inconnue s'est produite", "Veuillez contacter le support pour plus de détails.")
    },
}

SUCCESS_MESSAGE = {
    "en": "Transaction processed successfully!",
    "fr": "Transaction traitée avec succès!"
}
