from django.test import TestCase, Client
from django.test.testcases import unittest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from drivers.models import Drivers, Grade, DriverGrade, GradeRequirement
from clients.models import Clients
from rides.models import ReviewRating, Rides

User = get_user_model()

class GradeAPITests(APITestCase):
    """Tests pour les endpoints API des grades"""
    
    def setUp(self):
       
        # Ajouter un token d'authentification dans les en-têtes
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer test_token')
        
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
        
        # Configurer le client API
        self.client = APIClient()
        self.client.force_authenticate(user=self.driver)

    
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
    
    def test_get_driver_grade(self):
        """Teste la récupération du grade actuel du chauffeur"""
        url = reverse('get_drivers_grades')
        
        # Simuler le comportement de filter_and_decode_token pour retourner un utilisateur valide
        with unittest.mock.patch('drivers.views.JWT.filter_and_decode_token') as mock_filter:
            mock_filter.return_value = (None, self.driver)  # Retourne le driver de test
                
            # Le client est déjà authentifié via force_authenticate dans setUp
            response = self.client.get(url)
            print(response.data)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Vérifie que la réponse contient les champs attendus
            self.assertIn('Data', response.data)
            self.assertIn('grade', response.data['Data'])

    
    def test_get_grade_evolution(self):
        """Teste la récupération de l'évolution des grades"""
        url = reverse('get_drivers_grades_evolution')
        
        # Simuler le comportement de filter_and_decode_token pour retourner un utilisateur valide
        with unittest.mock.patch('drivers.views.JWT.filter_and_decode_token') as mock_filter:
            mock_filter.return_value = (None, self.driver)  # Retourne le driver de test
            
            response = self.client.get(url)
            print(response.data)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Vérifier la structure de base de la réponse
            self.assertIn('current_grade', response.data)
            self.assertIn('next_grade', response.data)
            self.assertIn('progress', response.data)
            self.assertIn('requirements', response.data)

    
    # def test_get_grade_history(self):
    #     """Teste la récupération de l'historique des grades"""
    #     # Ajouter un ancien grade
    #     old_grade = Grade.objects.create(
    #         name='Test',
    #         display_name='Test',
    #         commission_rate=25.0,
    #         is_active=False
    #     )
        
    #     old_driver_grade = DriverGrade.objects.create(
    #         driver=self.driver,
    #         grade=old_grade,
    #         is_current=False,
    #         assigned_at='2022-01-01T00:00:00Z',
    #         unassigned_at='2023-01-01T00:00:00Z'
    #     )
        
    #     url = reverse('driver-grade-history')
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(len(response.data), 2)  # Ancien grade + grade actuel
        
    #     # Vérifier que les grades sont triés par date d'attribution décroissante
    #     self.assertEqual(response.data[0]['grade']['name'], 'Standard')
    #     self.assertEqual(response.data[1]['grade']['name'], 'Test')
    
    def test_unauthorized_access(self):
        """Teste l'accès non autorisé aux endpoints protégés"""
        # Se déconnecter
        self.client.force_authenticate(user=None)
        
        urls = [
            reverse('get_drivers_grades'),
            reverse('get_drivers_grades_evolution')
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
