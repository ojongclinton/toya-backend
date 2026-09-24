# WebSocket Testing Guide - ELYFT Toya Backend

## 📋 Vue d'ensemble

Ce guide explique comment tester le WebSocket de tracking en temps réel pour les courses.

## 🚀 Installation

### 1. Installer les dépendances de test

```bash
pip install -r requirements-test.txt
```

Ou manuellement :
```bash
pip install pytest pytest-django pytest-asyncio pytest-cov
```

### 2. Vérifier la configuration

Le fichier `pytest.ini` est déjà configuré à la racine du projet.

## 🧪 Exécuter les tests

### Tests WebSocket (navigation)

```bash
# Tous les tests WebSocket
pytest navigation/tests.py -v

# Un test spécifique
pytest navigation/tests.py::TestRideTrackingConsumer::test_websocket_connect_success -v

# Avec couverture de code
pytest navigation/tests.py --cov=navigation --cov-report=html

# Mode verbeux avec output
pytest navigation/tests.py -v -s
```

### Tests REST (rides)

```bash
# Tous les tests REST
python manage.py test rides.tests.ClientTrackRidesTestCase

# Ou avec pytest
pytest rides/tests.py -v
```

### Tous les tests

```bash
# Tous les tests du projet
pytest -v

# Avec couverture
pytest --cov=. --cov-report=html
```

## 📊 Structure des tests WebSocket

### Tests créés (12 tests)

1. **Connexion & Autorisation**
   - `test_websocket_connect_success` - Connexion réussie
   - `test_websocket_connect_unauthorized` - Client non autorisé
   - `test_websocket_connect_unauthenticated` - Utilisateur non authentifié

2. **Actions client**
   - `test_websocket_receive_refresh_action` - Rafraîchir les données
   - `test_websocket_receive_ping_action` - Keep-alive
   - `test_websocket_invalid_json` - JSON invalide

3. **Broadcast temps réel**
   - `test_websocket_location_update_broadcast` - Mise à jour position
   - `test_websocket_route_update_broadcast` - Mise à jour route

4. **Gestion d'erreurs**
   - `test_websocket_invalid_ride_status` - Statut invalide
   - `test_websocket_no_driver_location` - Position indisponible

5. **Cas avancés**
   - `test_websocket_multiple_clients_same_ride` - Plusieurs clients

## 🔧 Configuration WebSocket

### URL WebSocket

```
ws://localhost:8000/ws/ride-tracking/<ride_id>/
```

### Exemple de connexion (JavaScript)

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/ride-tracking/${rideId}/`);

ws.onopen = () => {
  console.log('Connected to ride tracking');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'tracking_data') {
    // Données initiales
    updateMap(data.driver_location, data.route_data);
  } else if (data.type === 'location_update') {
    // Mise à jour position
    updateDriverMarker(data.driver_location);
  }
};

// Refresh manuel
ws.send(JSON.stringify({ action: 'refresh' }));

// Keep-alive
setInterval(() => {
  ws.send(JSON.stringify({ action: 'ping' }));
}, 30000);
```

## 📈 Comparaison REST vs WebSocket

### REST Polling (actuel)
```bash
# Endpoint REST
GET /rides/client/track/<ride_id>

# Requêtes : ~180 par course (15 min × 12 req/min)
# Coût : Élevé sur GCP
```

### WebSocket (nouveau)
```bash
# WebSocket
ws://localhost:8000/ws/ride-tracking/<ride_id>/

# Connexions : 1 par course
# Push : Seulement quand position change (~10-20 par course)
# Économie : 70-90% de réduction des coûts
```

## 🐛 Debugging

### Activer les logs WebSocket

Dans `settings.py` :
```python
LOGGING = {
    'loggers': {
        'channels': {
            'level': 'DEBUG',
        },
    },
}
```

### Tester manuellement avec wscat

```bash
# Installer wscat
npm install -g wscat

# Se connecter
wscat -c "ws://localhost:8000/ws/ride-tracking/<ride_id>/"

# Envoyer un message
> {"action": "refresh"}
```

## ✅ Checklist avant production

- [ ] Tous les tests passent
- [ ] WebSocket configuré dans `asgi.py`
- [ ] Channel layer configuré (Redis)
- [ ] Tests de charge effectués
- [ ] Monitoring en place
- [ ] Documentation API mise à jour

## 📚 Ressources

- [Django Channels Documentation](https://channels.readthedocs.io/)
- [Pytest Asyncio](https://pytest-asyncio.readthedocs.io/)
- [WebSocket Testing](https://channels.readthedocs.io/en/stable/topics/testing.html)

## 🆘 Support

Pour toute question, consulter :
- Tests existants dans `navigation/tests.py`
- Consumer dans `navigation/consumers.py`
- Documentation Channels
