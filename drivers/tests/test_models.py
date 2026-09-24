import os
import tempfile
from datetime import datetime, timedelta
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from drivers.models import Drivers, Vehicle, Subscription, Grade, GradeRequirement, DriverGrade

# Désactiver le stockage des fichiers médias pendant les tests
MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class GradeModelTests(TestCase):
    """Tests pour les modèles du système de grades"""
    
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
            value=50,
            description='Effectuer au moins 50 courses'
        )
    
    def test_grade_creation(self):
        """Teste la création d'un grade"""
        self.assertEqual(str(self.grade_standard), 'Standard')
        self.assertEqual(self.grade_standard.commission_rate, 20.0)
        self.assertTrue(self.grade_standard.is_active)
    
    def test_grade_requirement_creation(self):
        """Teste la création d'une exigence de grade"""
        self.assertEqual(str(self.rating_req), 'Bronze: Note moyenne minimale >= 4.5')
        self.assertEqual(self.rating_req.requirement_type, 'rating')
        self.assertEqual(self.rating_req.comparison_operator, '>=')
    
    def test_driver_grade_assignment(self):
        """Teste l'attribution d'un grade à un chauffeur"""
        # Créer un chauffeur
        driver = Drivers.objects.create(
            username='testdriver',
            first_name='Test',
            last_name='Driver',
            phone_number='+2250700000001',
            password='testpass123'
        )
        
        # Attribuer un grade au chauffeur
        driver_grade = DriverGrade.objects.create(
            driver=driver,
            grade=self.grade_standard,
            is_current=True
        )
        
        self.assertEqual(driver_grade.driver, driver)
        self.assertEqual(driver_grade.grade, self.grade_standard)
        self.assertTrue(driver_grade.is_current)
        self.assertIsNotNone(driver_grade.assigned_at)

    def test_new_driver_gets_standard_grade(self):
        """
        Vérifie qu'un nouveau chauffeur est automatiquement associé au grade Standard.
        """
        # Créer un chauffeur
        driver = Drivers.objects.create(
            username='testdriver1',
            email='testdriver1@example.com',
            user_type='drivers',
            first_name='Test',
            last_name='Driver',
            phone_number='+2250700000001',
            password='testpass123',
            is_available=True
        )
        
        # Vérifier que le chauffeur a bien un grade
        self.assertTrue(hasattr(driver, 'grades'), "Le chauffeur devrait avoir une relation 'grades'")
        
        # Récupérer le grade actuel du chauffeur
        current_grade = driver.grades.filter(is_active=True).first()
        
        # Vérifier qu'un grade a été attribué
        self.assertIsNotNone(current_grade, "Le chauffeur devrait avoir un grade actuel")
        
        # Vérifier que c'est bien le grade Standard
        self.assertEqual(
            current_grade.name, 
            'Standard',
            "Le chauffeur devrait avoir le grade Standard par défaut"
        )
        
        # Vérifier que le grade est marqué comme actuel
        self.assertTrue(
            current_grade.is_active, 
            "Le grade devrait être marqué comme actuel"
        )

# Nettoyage après les tests
def tearDownModule():
    import shutil
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
