import os 
from celery import Celery 
from celery.schedules import crontab 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
app = Celery('toyabackend')

# Configuration depuis les paramètres Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configuration des tâches périodiques
app.conf.beat_schedule = {
    # Mise à jour quotidienne des grades des chauffeurs à minuit
    'update-drivers-grades-daily': {
        'task': 'drivers.tasks.update_drivers_grades_task',
        'schedule': crontab(hour=0, minute=0),  # Tous les jours à minuit
        'options': {'expires': 60 * 60 * 23},  # Expire après 23h
        'args': (),
        'kwargs': {'force_update': False},
    },
}

# Découverte automatique des tâches dans les applications installées
app.autodiscover_tasks()