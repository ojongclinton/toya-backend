import os
import tempfile
from datetime import datetime, timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from clients.models import Clients
from drivers.models import Drivers, Grade, DriverGrade, GradeRequirement
from drivers.tasks import update_drivers_grades_task
from rides.models import ReviewRating, Rides

# Désactiver le stockage des fichiers médias pendant les tests
MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=MEDIA_ROOT, CELERY_TASK_ALWAYS_EAGER=True)
class GradeTaskTests(TestCase):
    """Tests pour la tâche Celery de mise à jour des grades"""
    
    def setUp(self):
        # Créer des grades de test
        self.grade_standard = Grade.objects.create(
            name='Standard',
            commission_rate=20.0,
            is_active=True
        )
        
        self.grade_bronze = Grade.objects.create(
            name='Bronze',
            commission_rate=18.0,
            is_active=True
        )
        
        # Créer des exigences pour le grade Bronze
        self.rating_req = GradeRequirement.objects.create(
            grade=self.grade_bronze,
            requirement_type=GradeRequirement.RATING,
            comparison_operator='>=',
            value=4.5,
            description='Avoir une note moyenne d\'au moins 4.5/5'
        )
        
        self.rides_req = GradeRequirement.objects.create(
            grade=self.grade_bronze,
            requirement_type=GradeRequirement.RIDES_COUNT,
            comparison_operator='>=',
            value=2,
            description='Effectuer au moins 2 courses'
        )
        
        # Créer un chauffeur
        self.driver1 = Drivers.objects.create(
            username='testdriver1',
            email='testdriver1@example.com',
            user_type='drivers',
            first_name='Test',
            last_name='Driver',
            phone_number='+2250700000001',
            password='testpass123',
            is_available=True
        )

        # Créer un autre chauffeur
        self.driver2 = Drivers.objects.create(
            username='testdriver2',
            email='testdriver2@example.com',
            user_type='drivers',
            first_name='Test',
            last_name='Driver',
            phone_number='+2250700000004',
            password='testpass123',
            is_available=True
        )
        
        # Créer un client pour les courses
        self.client_user = Clients.objects.create(
            username='testclient1',
            email='testclient1@example.com',
            user_type='client',
            first_name='Test',
            last_name='Client',
            phone_number='+237654542121',
            password='testpass123'
        )
        
        # Attribuer le grade standard au chauffeur
        self.driver_grade = DriverGrade.objects.create(
            driver=self.driver1,
            grade=self.grade_standard,
            is_current=True,
            assigned_at=timezone.now()
        )
        self.driver_grade = DriverGrade.objects.create(
            driver=self.driver2,
            grade=self.grade_standard,
            is_current=True,
            assigned_at=timezone.now()
        )
        
        # Ajouter le grade au chauffeur via la relation M2M
        self.driver1.grades.add(self.grade_standard, through_defaults={'is_current': True, 'assigned_at': timezone.now()})
        self.driver2.grades.add(self.grade_standard, through_defaults={'is_current': True, 'assigned_at': timezone.now()})
        
        # Vider le cache avant chaque test
        cache.clear()

    def create_ride(self, driver_id, client_id, status='completed', rating=None, final_price=2500.0):
        """Crée une course de test
        
        Args:
            driver_id: Instance du chauffeur
            client_id: Instance du client
            status: Statut de la course (default: 'completed')
            rating: Note à attribuer (optionnel)
            final_price: Prix final de la course (default: 2500.0)
            
        Returns:
            Instance de Rides créée
        """
        ride = Rides.objects.create(
            driver_id=driver_id,
            client_id=client_id,
            status=status,
            start_location='Point A',
            end_location='Point B',
            lon_start_location=-4.0333,
            lat_start_location=5.3543,
            lon_end_location=-4.0333,
            lat_end_location=5.3543,
            distance=5.0,
            final_price=final_price,
            mode_of_payments='cash',
            prestation='economy'
        )
        
        if rating and status == 'completed':
            ReviewRating.objects.create(
                rides_id=ride,
                driver_id=driver_id,
                client_id=client_id,
                rating=rating,
                comment='Test comment'
            )
        
        return ride
    
    def test_update_drivers_grades_task(self):
        """Teste la tâche de mise à jour des grades"""
        # Appeler la tâche initiale
        result = update_drivers_grades_task(force_update=True)
        print('result first run: ', result)
        
        # Vérifier que la tâche s'est exécutée avec succès
        self.assertEqual(result['total_processed'], 2)  # 2 chauffeurs
        
        # Vérifier que les grades n'ont pas changé (car les exigences ne sont pas remplies)
        self.assertEqual(
            DriverGrade.objects.get(driver=self.driver1, is_current=True).grade,
            self.grade_standard
        )
        
        # Créer 2 courses complétées avec des notes élevées pour atteindre le grade Bronze
        # - Note moyenne de 5.0 (2x5 étoiles)
        # - 2 courses (le minimum)
        # - Revenu total de 300 000 FCFA (dépassant le seuil de 250 000 FCFA)
        
        # Création des courses
        self.create_ride(
            driver_id=self.driver1,
            client_id=self.client_user,
            status='completed',
            rating=5,
            final_price=150000  # 150 000 FCFA
        )
        
        self.create_ride(
            driver_id=self.driver1,
            client_id=self.client_user,
            status='completed',
            rating=5,
            final_price=150000  # 150 000 FCFA (total 300 000 FCFA)
        )
        
        # Vérifier que les métriques sont correctes avant la mise à jour
        from drivers.services.grade_service import GradeEvaluationService
        metrics = GradeEvaluationService.evaluate_driver_metrics(self.driver1)
        self.assertEqual(metrics['rating'], 5.0)  # 2x5 étoiles = moyenne de 5.0
        self.assertEqual(metrics['rides_count'], 2)  # 2 courses créées
        self.assertEqual(metrics['revenue'], 300000)  # 2 x 150 000 FCFA
        
        # Réexécuter la tâche
        result = update_drivers_grades_task(force_update=True)
        print('result second run: ', result)
        
        # Vérifier que le chauffeur 1 a été mis à jour vers le grade Bronze
        driver1_grade = DriverGrade.objects.get(driver=self.driver1, is_current=True)
        self.assertEqual(driver1_grade.grade, self.grade_bronze)
        
        # Vérifier que l'ancien grade n'est plus actif
        self.assertEqual(
            DriverGrade.objects.filter(driver=self.driver1, is_current=True).count(),
            1
        )
        
        # Vérifier que le chauffeur 2 est toujours au grade Standard
        self.assertEqual(
            DriverGrade.objects.get(driver=self.driver2, is_current=True).grade,
            self.grade_standard
        )


# Nettoyage après les tests
def tearDownModule():
    import shutil
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
