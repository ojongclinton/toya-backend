from datetime import datetime, timedelta
from django.test import TestCase, override_settings
from django.utils import timezone

from clients.models import Clients
from drivers.models import Drivers, Grade, GradeRequirement, DriverGrade
from drivers.services.grade_service import GradeEvaluationService
from rides.models import ReviewRating, Rides

class GradeEvaluationServiceTests(TestCase):
    """Tests pour le service d'évaluation des grades"""
    
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
        self.driver = Drivers.objects.create(
            username='testdriver1',
            email='testdriver1@example.com',
            user_type='drivers',
            first_name='Test',
            last_name='Driver',
            phone_number='+2250700000001',
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
            driver=self.driver,
            grade=self.grade_standard,
            is_current=True,
            assigned_at=timezone.now()
        )
        
        # Ajouter le grade au chauffeur via la relation M2M
        self.driver.grades.add(self.grade_standard, through_defaults={'is_current': True, 'assigned_at': timezone.now()})
    
    def create_ride(self, status='completed', rating=None):
        """Crée une course de test"""
        ride = Rides.objects.create(
            driver_id=self.driver,
            client_id=self.client_user,
            status=status,
            start_location='Point A',
            end_location='Point B',
            lon_start_location=-4.0333,
            lat_start_location=5.3543,
            lon_end_location=-4.0333,
            lat_end_location=5.3543,
            distance=5.0,
            final_price=2500.0,
            mode_of_payments='cash',
            prestation='economy'
        )
        
        if rating and status == 'completed':
            ReviewRating.objects.create(
                rides_id=ride,
                driver_id=self.driver,
                client_id=self.client_user,
                rating=rating,
                comment='Test comment'
            )
        
        return ride
    
    def test_evaluate_driver_grade(self):
        """Teste l'évaluation du grade d'un chauffeur"""
        # Créer 2 courses complétées avec une note de 4
        self.create_ride(status='completed', rating=5)
        self.create_ride(status='completed', rating=4)
        
        # Récupérer le chauffeur
        driver = Drivers.objects.get(id=self.driver.id)
        
        # Évaluer les métriques
        metrics = GradeEvaluationService.evaluate_driver_metrics(driver)
        
        # Vérifier que les métriques sont correctes
        self.assertEqual(metrics['rating'], 4.5)
        self.assertEqual(metrics['rides_count'], 2)
        
        # Obtenir le grade correspondant aux métriques
        new_grade = GradeEvaluationService.get_grade_for_metrics(metrics)
        self.assertIsNotNone(new_grade)
        self.assertEqual(new_grade.name, 'Bronze')
        
        # Mettre à jour le grade du chauffeur
        success, message = GradeEvaluationService.update_driver_grade(driver, new_grade)
        
        # Vérifier que la mise à jour a réussi
        self.assertTrue(success)
        
        # Vérifier que l'ancien grade a été marqué comme non actif
        old_grade = DriverGrade.objects.get(driver=driver, grade=self.grade_standard)
        self.assertFalse(old_grade.is_current)
        self.assertIsNotNone(old_grade.unassigned_at)
        
        # Vérifier que le nouveau grade a été attribué
        new_driver_grade = DriverGrade.objects.get(driver=driver, grade=self.grade_bronze)
        self.assertTrue(new_driver_grade.is_current)
        self.assertIsNotNone(new_driver_grade.assigned_at)
    
    def test_evaluate_driver_grade_not_qualified(self):
        """Teste qu'un chauffeur non qualifié ne change pas de grade"""
        # Créer une seule course avec une note moyenne basse
        self.create_ride(status='completed', rating=3.0)
        
        # Récupérer le chauffeur
        driver = Drivers.objects.get(id=self.driver.id)
        
        # Évaluer les métriques
        metrics = GradeEvaluationService.evaluate_driver_metrics(driver)
        
        # Vérifier que les métriques sont correctes
        self.assertEqual(metrics['rating'], 3.0)
        self.assertEqual(metrics['rides_count'], 1)
        
        # Obtenir le grade correspondant aux métriques
        grade = GradeEvaluationService.get_grade_for_metrics(metrics)
        progress = GradeEvaluationService.get_next_grade_progress(driver)
        
        # Vérifier qu'aucun nouveau grade n'est attribué (car pas assez de courses)
        self.assertEqual(grade.name, 'Standard')
        self.assertEqual(progress['next_grade']['name'], 'Bronze')
        self.assertEqual(progress['current_grade']['name'], grade.name)
        
        # Vérifier que le grade actuel est toujours Standard
        current_grade = DriverGrade.objects.get(driver=driver, is_current=True)
        self.assertEqual(current_grade.grade.name, 'Standard')
    
    def test_get_next_grade_progress(self):
        """Teste la récupération de la progression vers le prochain grade"""
        # Créer une course complétée avec une note de 5.0
        self.create_ride(status='completed', rating=5.0)
        
        # Récupérer le chauffeur
        driver = Drivers.objects.get(id=self.driver.id)
        
        # Obtenir la progression
        progress = GradeEvaluationService.get_next_grade_progress(driver)
        
        # Vérifier les données de progression
        self.assertTrue(progress['has_grade'])
        self.assertEqual(progress['current_grade']['name'], 'Standard')
        self.assertEqual(progress['next_grade']['name'], 'Bronze')
        
        # Vérifier les métriques
        self.assertIn('metrics', progress)
        self.assertEqual(progress['metrics']['rides_count'], 1)
        self.assertEqual(progress['metrics']['rating'], 5.0)
        
        # Vérifier les exigences
        self.assertIn('requirements', progress)
        self.assertGreaterEqual(len(progress['requirements']), 1)
        
        # Vérifier la progression des exigences
        for req in progress['requirements']:
            if req['requirement_type'] == 'rides_count':
                self.assertEqual(req['current_value'], 1)
                self.assertEqual(float(req['required_value']), 2)  # No courses requises pour le grade Bronze
            elif req['requirement_type'] == 'rating':
                self.assertEqual(req['current_value'], 5.0)
                self.assertEqual(float(req['required_value']), 4.5)
