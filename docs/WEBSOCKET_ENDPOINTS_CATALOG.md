# Catalogue Complet des Endpoints WebSocket - ELYFT Toya Backend

## 📋 Vue d'ensemble

Ce document recense **TOUS** les endpoints WebSocket disponibles dans le backend ELYFT, leur statut (actif/obsolète), leur utilisation et des exemples d'intégration.

**Date de mise à jour:** 2026-01-16  
**Total d'endpoints:** 6

---

## ⚠️ IMPORTANT : Différence entre Notifications et Ride Status

Le backend dispose de **2 endpoints distincts** pour les événements de course, ce qui peut créer de la confusion :

### 🔔 `ws/notifications/<user_id>/` - Notifications Générales
- **Objectif:** Centre de notifications pour TOUS les types d'événements
- **Déclenchement:** Automatique via Django Signal (enregistrement DB puis broadcast)
- **Utilisation:** Badge notifications, historique, centre de notifications
- **Persistance:** ✅ Sauvegardé en base de données

### 🚗 `ws/ride-status/` - Statut Course Temps Réel
- **Objectif:** Mises à jour temps réel de l'interface course active uniquement
- **Déclenchement:** Manuel via `group_send` dans `rides/views.py`
- **Utilisation:** Écran course active, mises à jour instantanées UI
- **Persistance:** ❌ Broadcast direct sans sauvegarde DB

### ⚠️ Duplication Actuelle
Quand un chauffeur accepte une course, **2 notifications sont envoyées** :
1. Via `ws/notifications/{user_id}/` (depuis `notifications/signals.py`)
2. Via `ws/ride-status/` (depuis `rides/views.py`)

**Recommandation Frontend:** Se connecter aux DEUX endpoints mais gérer la duplication côté client pour éviter d'afficher 2 fois la même notification.

---

## 🟢 ENDPOINTS ACTIFS (Utilisés dans le backend)

### 1. **Notifications WebSocket** ✅ ACTIF

**Endpoint:** `ws://domain/ws/notifications/<user_id>/`

**Consumer:** `notifications/consumers.py` → `NotificationConsumer`

**Type:** AsyncWebsocketConsumer

**Utilisation:** 
- ✅ **Automatique via Django Signals** (`notifications/signals.py`)
- Déclenché automatiquement à chaque création de notification en DB
- Broadcast vers le canal `notifications_{user_id}`

**Fonctionnalité:**
- Envoie des notifications en temps réel aux utilisateurs
- Types de notifications supportés:
  - `ride_started` - Course démarrée
  - `ride_accepted` - Course acceptée par chauffeur
  - `ride_completed` - Course terminée
  - `ride_canceled` - Course annulée
  - `payment_success` - Paiement réussi
  - `payment_failed` - Paiement échoué
  - `subscription_payment` - Paiement abonnement
  - `new_ride` - Nouvelle course
  - `support_ticket` - Ticket support
  - `message_received` - Message reçu
  - `support_message_received` - Message support reçu
  - `new_review` - Nouvel avis

**Paramètres URL:**
- `user_id` (UUID) - ID de l'utilisateur (client ou chauffeur)

**Messages reçus:**
```json
{
  "message": "Your ride has been accepted by the driver",
  "event_id": "ride-uuid-here",
  "notification_type": "ride_accepted",
  "additional_data": {
    "rides_drivers_closed": "driver-uuid"
  }
}
```

**Exemple d'intégration:**
```javascript
const userId = getCurrentUserId();
const ws = new WebSocket(`wss://pre-prod.toya-vtc.com/ws/notifications/${userId}/`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  // Afficher dans le centre de notifications
  addToNotificationCenter(data);
  incrementNotificationBadge();
  
  // Optionnel: Afficher toast pour notifications importantes
  if (['ride_accepted', 'payment_success'].includes(data.notification_type)) {
    showToast(data.message);
  }
};
```

**Cas d'usage:** Centre de notifications, badge, historique persistant

**Statut:** ✅ **PRODUCTION - UTILISÉ ACTIVEMENT**

---

### 2. **Ride Status Updates** ✅ ACTIF (NOUVEAU)

**Endpoint:** `ws://domain/ws/ride-status/`

**Consumer:** `rides/consumers.py` → `RideStatusConsumer`

**Type:** AsyncWebsocketConsumer

**Authentification:** ✅ **JWT REQUIS** via query string

**⚠️ IMPORTANT - Authentification:**
```javascript
// ✅ CORRECT - Token dans query string
const token = localStorage.getItem('jwt_token');
const ws = new WebSocket(`wss://pre-prod.toya-vtc.com/ws/ride-status/?token=${token}`);

// ❌ INCORRECT - Sans token (erreur 403/4001)
const ws = new WebSocket('wss://pre-prod.toya-vtc.com/ws/ride-status/');

// ❌ INCORRECT - Avec user_id dans URL (erreur 500)
const ws = new WebSocket(`wss://pre-prod.toya-vtc.com/ws/ride-status/${userId}/`);
```

**Utilisation:**
- ✅ **Broadcasts manuels dans `rides/views.py`**
- Utilisé dans 5 endpoints:
  - `driver_accept_rides()` - Ligne ~602
  - `driver_start_rides()` - Ligne ~792
  - `driver_complete_rides()` - Ligne ~728
  - `client_cancel_rides()` - Ligne ~192
  - `driver_cancel_rides()` - Ligne ~673

**Fonctionnalité:**
- Mises à jour en temps réel du statut des courses
- Canal utilisateur-spécifique: `ride_updates_{user_id}` (détecté automatiquement via JWT)
- Connexion persistante (pas besoin de ride_id dans URL)

**Actions supportées:**
- `ping` - Keep-alive
- `get_active_rides` - Récupérer les courses actives

**Types de messages:**
- `connection_established` - Confirmation de connexion
- `ride_accepted` - Course acceptée
- `ride_started` - Course démarrée
- `ride_completed` - Course terminée
- `ride_cancelled` - Course annulée
- `pong` - Réponse au ping

**Exemple de message reçu:**
```json
{
  "type": "ride_accepted",
  "ride_id": "ride-uuid",
  "driver_id": "driver-uuid",
  "driver_name": "John Doe",
  "accepted_time": "2026-01-16T06:30:00Z",
  "message": "Your ride has been accepted by a driver"
}
```

**Exemple d'intégration:**
```javascript
// 1. Récupérer le token JWT
const token = localStorage.getItem('jwt_token'); // ou votre méthode de stockage

// 2. Connexion avec token dans query string
const ws = new WebSocket(`wss://pre-prod.toya-vtc.com/ws/ride-status/?token=${token}`);

ws.onopen = () => {
  console.log('✅ Connecté au ride status');
  
  // Envoyer ping toutes les 30s
  setInterval(() => {
    ws.send(JSON.stringify({ action: 'ping' }));
  }, 30000);
};

ws.onerror = (error) => {
  console.error('❌ Erreur WebSocket:', error);
};

ws.onclose = (event) => {
  if (event.code === 4001) {
    console.error('🔒 Authentification échouée - Token invalide ou expiré');
  }
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'connection_established':
      console.log('User ID:', data.user_id);
      break;
      
    case 'ride_accepted':
      // Mettre à jour l'interface course active
      showDriverInfo(data.driver_name, data.driver_id);
      updateRideStatus('accepted_by_driver');
      navigateToTrackingScreen(data.ride_id);
      break;
      
    case 'ride_started':
      updateRideStatus('in_progress');
      startRideTimer(data.start_time);
      break;
      
    case 'ride_completed':
      updateRideStatus('completed');
      showRatingScreen(data.ride_id, data.final_price);
      break;
      
    case 'ride_cancelled':
      updateRideStatus('cancelled');
      showCancellationMessage(data.cancelled_by);
      navigateToHomeScreen();
      break;
  }
};
```

**Cas d'usage:** Interface course active, mises à jour UI temps réel

**Statut:** ✅ **PRODUCTION - IMPLÉMENTÉ RÉCEMMENT**

---

### 3. **Ride Location Tracking** ✅ ACTIF

**Endpoint:** `ws://domain/ws/ride-tracking/<ride_id>/`

**Consumer:** `navigation/consumers.py` → `RideTrackingConsumer`

**Type:** AsyncWebsocketConsumer

**Utilisation:**
- ⚠️ **PAS de broadcasts backend automatiques détectés**
- Consumer prêt mais nécessite intégration dans `navigation/views.py`
- Authentification JWT requise

**Fonctionnalité:**
- Tracking en temps réel de la position du chauffeur
- Informations de route et itinéraire
- Vérification d'autorisation (seul le client de la course peut tracker)

**Paramètres URL:**
- `ride_id` (UUID) - ID de la course à tracker

**Actions supportées:**
- `refresh` - Rafraîchir les données de tracking
- `ping` - Keep-alive

**Types de messages:**
- `tracking_data` - Données initiales de tracking
- `location_update` - Mise à jour position chauffeur
- `route_update` - Mise à jour itinéraire
- `error` - Erreur (ride non disponible, pas de chauffeur, etc.)

**Exemple de message:**
```json
{
  "type": "tracking_data",
  "ride_status": "in_progress",
  "driver_location": {
    "lat": -12.12345,
    "lon": -77.03456,
    "address": "Rue 023 Douala Akwa",
    "timestamp": "2026-01-16T06:30:00Z"
  },
  "route_data": {
    "route_type": "dropoff",
    "total_distance_km": 5.2,
    "total_duration": "15 mins",
    "itinerary": [...]
  }
}
```

**Exemple d'intégration:**
```javascript
const rideId = getCurrentRideId();
const ws = new WebSocket(`wss://pre-prod.toya-vtc.com/ws/ride-tracking/${rideId}/`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'tracking_data') {
    initializeMap(data.driver_location, data.route_data);
  } else if (data.type === 'location_update') {
    updateDriverMarker(data.driver_location);
  }
};

// Rafraîchir manuellement
ws.send(JSON.stringify({ action: 'refresh' }));
```

**⚠️ ATTENTION:** Ce consumer est prêt mais les broadcasts depuis `navigation/views.py` ne sont pas implémentés. Il faut ajouter des `group_send` quand le chauffeur met à jour sa position.

**Statut:** ✅ **PRODUCTION - PARTIELLEMENT UTILISÉ**

---

## 🟡 ENDPOINTS SEMI-ACTIFS (Consumer prêt, broadcasts limités)

### 4. **Conversation/Chat** 🟡 SEMI-ACTIF

**Endpoint:** `ws://domain/ws/conversation/<room_name>/`

**Consumer:** `conversation/consumers.py` → `ChatConsumer`

**Type:** WebsocketConsumer (synchrone)

**Utilisation:**
- ✅ Broadcast interne dans le consumer lui-même
- ⚠️ Pas d'authentification JWT
- Messages sauvegardés en DB via `ConversationSerializer`

**Fonctionnalité:**
- Chat en temps réel entre client et chauffeur pendant une course
- Création automatique de notifications DB
- Canal: `chat_{room_name}`

**Paramètres URL:**
- `room_name` - Nom de la room (généralement `ride_id`)

**Format message à envoyer:**
```json
{
  "message": "Bonjour, je suis arrivé",
  "sender_id": "user-uuid",
  "receiver_id": "user-uuid",
  "rides_id": "ride-uuid"
}
```

**Format message reçu:**
```json
{
  "message": "Bonjour, je suis arrivé",
  "sender_id": "sender-uuid",
  "receiver_id": "receiver-uuid",
  "rides_id": "ride-uuid"
}
```

**Exemple d'intégration:**
```javascript
const rideId = getCurrentRideId();
const ws = new WebSocket(`wss://pre-prod.toya-vtc.com/ws/conversation/${rideId}/`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.error) {
    console.error(data.error);
  } else {
    displayMessage(data.message, data.sender_id);
  }
};

// Envoyer un message
function sendMessage(text) {
  ws.send(JSON.stringify({
    message: text,
    sender_id: currentUserId,
    receiver_id: otherUserId,
    rides_id: rideId
  }));
}
```

**⚠️ PROBLÈMES IDENTIFIÉS:**
- Pas d'authentification JWT (n'importe qui peut se connecter)
- Consumer synchrone (devrait être async pour meilleures performances)
- Validation des champs requise côté client

**Statut:** 🟡 **PRODUCTION - FONCTIONNE MAIS NÉCESSITE AMÉLIORATIONS**

---

### 5. **Support Chat** 🟡 SEMI-ACTIF

**Endpoint:** `ws://domain/ws/support/<room_name>/`

**Consumer:** `support/consumers.py` → `SupportConsumer`

**Type:** WebsocketConsumer (synchrone)

**Utilisation:**
- ✅ Broadcast interne dans le consumer
- ⚠️ Pas d'authentification JWT
- Messages sauvegardés en DB via `SupportConversationSerializer`

**Fonctionnalité:**
- Chat en temps réel entre utilisateur et support
- Création automatique de notifications DB
- Canal: `chat_{room_name}`

**Paramètres URL:**
- `room_name` - Nom de la room (généralement `ticket_id`)

**Format message à envoyer:**
```json
{
  "message": "J'ai un problème avec ma course",
  "sender_id": "user-uuid",
  "receiver_id": "support-uuid",
  "ticket_id": "ticket-uuid"
}
```

**Format message reçu:**
```json
{
  "message": "J'ai un problème avec ma course",
  "sender_id": "sender-uuid",
  "receiver_id": "receiver-uuid",
  "ticket_id": "ticket-uuid"
}
```

**Exemple d'intégration:**
```javascript
const ticketId = getCurrentTicketId();
const ws = new WebSocket(`wss://pre-prod.toya-vtc.com/ws/support/${ticketId}/`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.error) {
    console.error(data.error);
  } else {
    displaySupportMessage(data.message, data.sender_id);
  }
};

// Envoyer un message au support
function sendSupportMessage(text) {
  ws.send(JSON.stringify({
    message: text,
    sender_id: currentUserId,
    receiver_id: supportUserId,
    ticket_id: ticketId
  }));
}
```

**⚠️ PROBLÈMES IDENTIFIÉS:**
- Identiques au chat conversation (pas d'auth, synchrone)

**Statut:** 🟡 **PRODUCTION - FONCTIONNE MAIS NÉCESSITE AMÉLIORATIONS**

---

## 🔴 ENDPOINTS SPÉCIALISÉS

### 6. **Payment Status Tracking** 🔴 SPÉCIALISÉ

**Endpoint:** `ws://domain/ws/payment/status/<transaction_id>/<user_id>/`

**Consumer:** `payments/consumers.py` → `PaymentStatusConsumer`

**Type:** AsyncWebsocketConsumer

**Utilisation:**
- ✅ Polling automatique interne (toutes les 20s pendant 130s max)
- Vérifie le statut de paiement via S3CashOutManager
- Validation UUID pour transaction_id et user_id

**Fonctionnalité:**
- Suivi en temps réel du statut d'une transaction de paiement
- Polling automatique côté serveur (pas besoin d'action client)
- Timeout après 130 secondes

**Paramètres URL:**
- `transaction_id` (UUID) - ID de la transaction
- `user_id` (UUID) - ID de l'utilisateur

**Statuts possibles:**
- `SUCCESS` - Paiement réussi
- `FAILED` - Paiement échoué
- `PENDING` - En attente
- `ERRORED` - Erreur
- `UNKNOWN` - Statut inconnu
- `Payment Status Timeout` - Timeout dépassé

**Format message reçu:**
```json
{
  "status": {
    "status": "SUCCESS",
    "message": {
      "fr": {
        "message_fr": "Paiement réussi",
        "solution_fr": "..."
      },
      "en": {
        "message_en": "Payment successful",
        "solution_en": "..."
      }
    }
  }
}
```

**Exemple d'intégration:**
```javascript
const transactionId = getTransactionId();
const userId = getCurrentUserId();
const ws = new WebSocket(
  `wss://pre-prod.toya-vtc.com/ws/payment/status/${transactionId}/${userId}/`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  const status = data.status.status || data.status;
  
  switch(status) {
    case 'SUCCESS':
      showPaymentSuccess();
      ws.close();
      break;
    case 'FAILED':
      showPaymentError(data.status.message);
      ws.close();
      break;
    case 'PENDING':
      showPaymentPending();
      break;
    case 'Payment Status Timeout':
      showTimeout();
      ws.close();
      break;
  }
};
```

**⚠️ NOTES IMPORTANTES:**
- Le polling est côté serveur (20s × 6 = 120s + timeout)
- Pas besoin d'envoyer de messages depuis le client
- La connexion se ferme automatiquement après timeout ou statut final

**Statut:** 🔴 **PRODUCTION - CAS D'USAGE SPÉCIFIQUE**

---

## ❌ ENDPOINTS OBSOLÈTES OU NON UTILISÉS

**Aucun endpoint obsolète détecté.** Tous les endpoints configurés sont utilisés ou prêts à l'emploi.

---

## 📊 Résumé par Statut

| Statut | Nombre | Endpoints |
|--------|--------|-----------|
| ✅ Actif (Production) | 3 | Notifications, Ride Status, Ride Tracking |
| 🟡 Semi-actif | 2 | Conversation, Support |
| 🔴 Spécialisé | 1 | Payment Status |
| ❌ Obsolète | 0 | Aucun |
| **TOTAL** | **6** | |

---

## 🔧 Configuration Requise

### Redis (Channel Layer)

Tous les WebSockets nécessitent Redis configuré dans `settings.py`:

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

### Serveur ASGI

Utiliser Daphne pour servir les WebSockets:

```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

### Authentification JWT

Les endpoints suivants utilisent JWT via `JWTAuthMiddlewareStack`:
- ✅ Ride Status (`ws/ride-status/`) - **Token requis dans query string: `?token=<jwt>`**
- ✅ Ride Tracking (`ws/ride-tracking/<ride_id>/`) - **Token requis dans query string: `?token=<jwt>`**

**Comment passer le token JWT:**
```javascript
const token = localStorage.getItem('jwt_token');
const ws = new WebSocket(`wss://domain/ws/ride-status/?token=${token}`);
```

**Codes d'erreur:**
- `4001` - Token invalide, expiré ou manquant
- `403` - Authentification échouée (pas de token)
- `500` - Erreur serveur (souvent dû à une URL incorrecte)

Les endpoints suivants **N'ONT PAS** d'authentification JWT:
- ⚠️ Notifications (`ws/notifications/<user_id>/`)
- ⚠️ Conversation (`ws/conversation/<room_name>/`)
- ⚠️ Support (`ws/support/<room_name>/`)
- ⚠️ Payment Status (`ws/payment/status/<transaction_id>/<user_id>/`)

---

## 🚨 Problèmes Identifiés & Recommandations

### 1. **Authentification manquante**
**Problème:** Plusieurs endpoints n'ont pas d'authentification JWT
**Endpoints concernés:** Notifications, Conversation, Support, Payment Status
**Risque:** N'importe qui peut se connecter avec un UUID valide
**Recommandation:** Ajouter JWT auth à tous les endpoints

### 2. **Consumers synchrones**
**Problème:** Conversation et Support utilisent `WebsocketConsumer` (synchrone)
**Impact:** Performances réduites sous charge
**Recommandation:** Migrer vers `AsyncWebsocketConsumer`

### 3. **Ride Tracking incomplet**
**Problème:** Consumer prêt mais pas de broadcasts depuis `navigation/views.py`
**Impact:** Position chauffeur pas mise à jour en temps réel
**Recommandation:** Ajouter `group_send` dans `update_driver_location()`

### 4. **Duplication Notifications**
**Problème:** Notifications envoyées via 2 canaux:
  - WebSocket Notifications (`ws/notifications/<user_id>/`)
  - WebSocket Ride Status (`ws/ride-status/`)
**Impact:** Possibles notifications en double pour les événements de course
**Explication:** 
  - `ws/notifications/` : Enregistre en DB puis broadcast (pour historique/badge)
  - `ws/ride-status/` : Broadcast direct sans DB (pour UI temps réel)
**Recommandation:** Frontend doit se connecter aux DEUX mais gérer la déduplication côté client. Chaque canal a un rôle distinct (voir section "Différence entre Notifications et Ride Status" en haut du document)

### 5. **Documentation manquante**
**Problème:** Aucune doc centralisée avant ce document
**Impact:** Confusion frontend, intégrations incorrectes
**Recommandation:** Maintenir ce document à jour

---

## 📝 Exemples d'Intégration Complète

### Scénario: Client demande une course

```javascript
// 1. Se connecter aux WebSockets nécessaires au démarrage de l'app
const wsNotifications = new WebSocket(
  `wss://pre-prod.toya-vtc.com/ws/notifications/${userId}/`
);
const wsRideStatus = new WebSocket(
  'wss://pre-prod.toya-vtc.com/ws/ride-status/'
);

// 2. Gérer les notifications générales (badge, centre de notifications)
wsNotifications.onmessage = (event) => {
  const data = JSON.parse(event.data);
  addToNotificationCenter(data);
  incrementNotificationBadge();
};

// 3. Gérer les mises à jour de statut course (UI temps réel)
wsRideStatus.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'ride_accepted') {
    // Chauffeur a accepté - Mettre à jour l'interface
    showDriverInfo(data.driver_name, data.driver_id);
    updateRideStatus('accepted_by_driver');
    
    // 4. Se connecter au tracking de position
    const wsTracking = new WebSocket(
      `wss://pre-prod.toya-vtc.com/ws/ride-tracking/${data.ride_id}/`
    );
    
    wsTracking.onmessage = (trackEvent) => {
      const trackData = JSON.parse(trackEvent.data);
      updateMapWithDriverLocation(trackData.driver_location);
    };
    
    // 5. Ouvrir le chat si nécessaire
    const wsChat = new WebSocket(
      `wss://pre-prod.toya-vtc.com/ws/conversation/${data.ride_id}/`
    );
  }
};

// 6. Demander la course via REST API
fetch('/api/rides/client/request', {
  method: 'POST',
  body: JSON.stringify(rideData)
});

// Note: Le client recevra 2 notifications pour "ride_accepted":
// - Une via wsNotifications (pour le badge/historique)
// - Une via wsRideStatus (pour l'UI temps réel)
// Gérer la déduplication côté client pour éviter d'afficher 2 fois
```

---

## 🔗 Fichiers de Référence

- **Configuration ASGI:** `core/asgi.py`
- **Middleware JWT:** `core/middleware.py`
- **Signals Notifications:** `notifications/signals.py`
- **Tests WebSocket:** `navigation/tests.py`, `README_WEBSOCKET_TESTS.md`
- **Documentation Ride Status:** `docs/WEBSOCKET_RIDE_STATUS_IMPLEMENTATION.md`

---

## ✅ Checklist Frontend

Pour chaque endpoint, vérifier:

- [ ] URL correcte (ws:// en dev, wss:// en prod)
- [ ] Paramètres URL corrects (UUIDs valides)
- [ ] Gestion des erreurs de connexion
- [ ] Reconnexion automatique en cas de déconnexion
- [ ] Keep-alive (ping/pong) si supporté
- [ ] Fermeture propre des connexions
- [ ] Gestion des messages d'erreur
- [ ] Tests sur réseau instable

---

**Dernière mise à jour:** 2026-01-16  
**Auteur:** Backend Team ELYFT  
**Version:** 1.0
