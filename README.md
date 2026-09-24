# Toya-Back-end

The Toya API is a complete solution for connecting private drivers and customers, designed to manage all the operations of a transport platform.

## Lancement avec Python
## Installation

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/ELYFT-UBIX/Toya-Back-end.git
   cd Toya-Back-end
   ```

2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Appliquer les migrations et lancer le serveur :
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Usage

- Accéder à l'application : [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Accéder à l'admin : [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)







## Lancement avec Docker

1. **Installer Docker et Docker Compose**  
   Assurez-vous que Docker et Docker Compose sont installés sur votre machine. Vous pouvez les télécharger ici :  
   - [Docker Desktop](https://www.docker.com/products/docker-desktop)  
   - [Docker Compose](https://docs.docker.com/compose/install/)

2. **Configurer les fichiers Docker**  
   Vérifiez que les fichiers suivants existent dans le projet :  
   - `Dockerfile`
   - `docker-compose.yml`

3. **Construire et lancer les conteneurs**  
   Exécutez les commandes suivantes pour démarrer l'application avec Docker :  
   ```bash
   docker-compose build
   docker-compose up
   ```

4. **Accéder à l'application**  
   Une fois les conteneurs démarrés, accédez à l'application via les URL suivantes :  
   - Application principale : [http://127.0.0.1:8000](http://127.0.0.1:8000)  
   - Interface d'administration : [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

5. **Arrêter les conteneurs**  
   Pour arrêter les conteneurs en cours d'exécution, utilisez :  
   ```bash
   docker-compose down
   ```



### Alerts
FutureWarning: You are using a Python version (3.10.19) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2026-10-04). Please upgrade to the latest Python version, or at least Python 3.11, to continue receiving updates for google.api_core past that date. #TODO #FIX_ME