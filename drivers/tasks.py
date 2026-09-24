"""
Tâches Celery pour le module drivers.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from django.db.models import Q

from drivers.models import Drivers, DriverGrade
from drivers.services.grade_service import GradeEvaluationService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def update_drivers_grades_task(self, driver_ids=None, force_update=False):
    """
    Tâche Celery pour mettre à jour les grades des chauffeurs.
    
    Args:
        driver_ids: Liste optionnelle d'IDs de chauffeurs à mettre à jour.
                   Si None, met à jour tous les chauffeurs.
        force_update: Si True, force la mise à jour même si le grade n'a pas changé.
                     Par défaut, ne met à jour que si nécessaire.
    
    Returns:
        dict: Résumé des mises à jour effectuées
    """
    try:
        # NOTE - Devra être amélioré avec le temps pour une meilleure gestion de grand nombres
        logger.info("Début de la mise à jour des grades des chauffeurs")
        
        # Déterminer la requête de base
        query = Drivers.objects.all()
        
        # Filtrer par IDs si spécifié
        if driver_ids:
            query = query.filter(id__in=driver_ids)
        
        # Si force_update est False, ne mettre à jour que les chauffeurs dont le grade a pu changer
        if not force_update:
            # Récupérer la date de la dernière mise à jour des grades
            last_grade_update = (
                DriverGrade.objects
                .filter(is_current=True)
                .order_by('-assigned_at')
                .values_list('assigned_at', flat=True)
                .first()
            )
            
            # Si des grades existent, filtrer les chauffeurs dont les données ont changé depuis
            if last_grade_update:
                query = query.filter(
                    Q(updated_at__gt=last_grade_update) |  # Données mises à jour
                    Q(drivergrade__isnull=True) |  # Pas encore de grade
                    ~Q(drivergrade__is_current=True)  # Grade actuel obsolète
                ).distinct()
        
        # Compter le nombre de chauffeurs à traiter
        total_drivers = query.count()
        logger.info(f"{total_drivers} chauffeurs à traiter pour la mise à jour des grades")
        
        # Mettre à jour les grades
        results = {
            'total_processed': 0,
            'grades_updated': 0,
            'errors': [],
            'start_time': timezone.now().isoformat(),
            'driver_ids_updated': []
        }
        
        # Traiter les chauffeurs par lots pour éviter les problèmes de mémoire
        batch_size = 50
        for i in range(0, total_drivers, batch_size):
            batch = query[i:i + batch_size]
            for driver in batch:
                try:
                    updated, message = GradeEvaluationService.evaluate_and_update_driver_grade(driver)
                    results['total_processed'] += 1
                    
                    if updated:
                        results['grades_updated'] += 1
                        results['driver_ids_updated'].append(str(driver.id))
                        logger.info(f"Grade mis à jour pour le chauffeur {driver.id}: {message}")
                    
                    # Envoyer une notification de progression périodiquement
                    if results['total_processed'] % 10 == 0:
                        self.update_state(
                            state='PROGRESS',
                            meta={
                                'processed': results['total_processed'],
                                'total': total_drivers,
                                'updated': results['grades_updated']
                            }
                        )
                except Exception as e:
                    error_msg = f"Erreur lors de la mise à jour du grade pour le chauffeur {driver.id}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    results['errors'].append({
                        'driver_id': str(driver.id) if driver else 'unknown',
                        'error': str(e)
                    })
        
        # Enregistrer les résultats
        results['end_time'] = timezone.now().isoformat()
        results['duration_seconds'] = (
            timezone.datetime.fromisoformat(results['end_time']) - 
            timezone.datetime.fromisoformat(results['start_time'])
        ).total_seconds()
        
        logger.info(
            f"Mise à jour des grades terminée. "
            f"Traités: {results['total_processed']}, "
            f"Mis à jour: {results['grades_updated']}, "
            f"Erreurs: {len(results['errors'])}"
        )
        
        return results
    
    except Exception as e:
        logger.error("Erreur lors de la mise à jour des grades des chauffeurs", exc_info=True)
        # Réessayer la tâche en cas d'échec
        raise self.retry(exc=e, countdown=60 * 5)  # Réessayer après 5 minutes


def schedule_daily_grade_updates():
    """
    Planifie la tâche de mise à jour quotidienne des grades.
    
    À appeler dans la configuration Celery (CELERY_BEAT_SCHEDULE).
    """
    from celery.schedules import crontab
    
    return {
        'update-drivers-grades-daily': {
            'task': 'drivers.tasks.update_drivers_grades_task',
            'schedule': crontab(hour=0, minute=0),  # Tous les jours à minuit
            'options': {'expires': 60 * 60 * 23},  # Expire après 23h
            'args': (),
            'kwargs': {'force_update': False},
        },
    }
