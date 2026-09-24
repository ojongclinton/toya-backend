# utils/language.py
from django.core.cache import cache

def get_user_language(user=None, device_id=None):
    """
    Récupère la langue d'un utilisateur.
    
    Priority:
    1. device_id (si fourni)
    2. user preference (si user fourni)
    3. Défaut: 'fr'
    """
    if device_id:
        cache_key = f"language_{device_id}"
        return cache.get(cache_key, 'fr')
    
    # Pour l'instant, retourner français par défaut
    # TODO: Ajouter champ language dans User model
    return 'fr'