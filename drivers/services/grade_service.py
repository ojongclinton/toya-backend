"""
Service d'évaluation et de gestion des grades des chauffeurs.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Tuple, List

from django.db import transaction
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone

from drivers.models import DriverGrade, Grade, GradeRequirement, Drivers
from drivers.serializers import GradeSerializer
from rides.models import Rides, ReviewRating
from referrals.models import ReferralsDrivers


class GradeEvaluationService:
    """
    Service pour évaluer et mettre à jour les grades des chauffeurs.
    """
    
    @classmethod
    def evaluate_driver_metrics(cls, driver: Drivers) -> Dict[str, float]:
        """
        Calcule les métriques d'un chauffeur nécessaires à l'évaluation du grade.
        
        Args:
            driver: Instance du chauffeur à évaluer
            
        Returns:
            Dict contenant les métriques du chauffeur
        """
        # Calcul de la note moyenne
        rating_avg = ReviewRating.objects.filter(
            driver_id=driver.id
        ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.0
        
        # Comptage du nombre de courses effectuées
        rides_count = Rides.objects.filter(
            driver_id=driver.id,
            status='completed'
        ).count()
        
        # Calcul du chiffre d'affaires total (en utilisant le montant payé par le client)
        revenue = Rides.objects.filter(
            driver_id=driver.id,
            status='completed'
        ).aggregate(total_revenue=Sum('final_price'))['total_revenue'] or Decimal('0.00')
        
        
        return {
            'rating': float(rating_avg) if rating_avg else 0.0,
            'rides_count': rides_count,
            'revenue': float(revenue) if revenue else 0.0,
        }
    
    @classmethod
    def get_grade_for_metrics(cls, metrics: Dict[str, float]) -> Optional[Grade]:
        """
        Détermine le grade approprié pour un ensemble de métriques données.
        
        Args:
            metrics: Dictionnaire des métriques du chauffeur
            
        Returns:
            Instance du Grade correspondant ou None si aucun grade ne correspond
        """
        # Récupérer tous les grades actifs triés par commission croissante (Standard → Platinum)
        grades = Grade.objects.filter(is_active=True).order_by('commission_rate')
        
        # Pour chaque grade, vérifier si le chauffeur remplit toutes les exigences
        for grade in grades:
            requirements = GradeRequirement.objects.filter(grade=grade)
            meets_all_requirements = True
            
            for req in requirements:
                driver_value = metrics.get(req.requirement_type, 0)
                
                # Appliquer l'opérateur de comparaison
                if req.comparison_operator == '>=':
                    if not (driver_value >= float(req.value)):
                        meets_all_requirements = False
                        break
                elif req.comparison_operator == '>':
                    if not (driver_value > float(req.value)):
                        meets_all_requirements = False
                        break
                elif req.comparison_operator == '==':
                    if not (driver_value == float(req.value)):
                        meets_all_requirements = False
                        break
            
            if meets_all_requirements:
                return grade
        
        return None
    
    @classmethod
    @transaction.atomic
    def update_driver_grade(cls, driver: Drivers, new_grade: Grade, reason: str = None) -> Tuple[bool, str]:
        """
        Met à jour le grade d'un chauffeur.
        
        Args:
            driver: Instance du chauffeur
            new_grade: Nouveau grade à attribuer
            reason: Raison du changement de grade (optionnel)
            
        Returns:
            Tuple (success: bool, message: str)
        """
        # Vérifier si le chauffeur a déjà un grade actif
        current_grade = DriverGrade.objects.filter(driver=driver, is_current=True).first()
        
        # Si le grade actuel est le même que le nouveau, ne rien faire
        if current_grade and current_grade.grade == new_grade:
            return False, f"Le chauffeur a déjà le grade {new_grade.name}"
        
        # Marquer l'ancien grade comme inactif
        if current_grade:
            current_grade.is_current = False
            current_grade.unassigned_at = timezone.now()
            current_grade.save()
        
        # Créer une nouvelle entrée pour le nouveau grade
        DriverGrade.objects.create(
            driver=driver,
            grade=new_grade,
            reason=reason or f"Mise à jour automatique du grade le {timezone.now().date()} suite à l'atteinte des exigences du grade {new_grade.name}",
            is_current=True
        )
        
        return True, f"Grade mis à jour vers {new_grade.name}"
    
    @classmethod
    def get_next_grade_progress(cls, driver: Drivers) -> Dict:
        """
        Calcule la progression vers le prochain grade.
        
        Args:
            driver: Instance du chauffeur
            
        Returns:
            Dictionnaire contenant les informations de progression
        """
        current_grade = DriverGrade.objects.filter(driver=driver, is_current=True).first()
        if not current_grade:
            return {
                'has_grade': False,
                'message': 'Aucun grade actif pour ce chauffeur'
            }
        
        # Récupérer les métriques actuelles du chauffeur
        metrics = cls.evaluate_driver_metrics(driver)
        
        # Récupérer le prochain grade possible (grade avec un meilleur taux de commission)
        next_grade = Grade.objects.filter(
            is_active=True,
            commission_rate__lt=current_grade.grade.commission_rate
        ).order_by('-commission_rate').first()
        
        if not next_grade:
            return {
                'has_grade': True,
                'current_grade': current_grade.grade.name,
                'is_highest': True,
                'message': f'Vous avez atteint le grade le plus élevé ({current_grade.grade.name})',
                'progress': 100
            }
        
        # Vérifier les exigences du prochain grade
        requirements = GradeRequirement.objects.filter(grade=next_grade)
        requirements_progress = []
        all_requirements_met = True
        
        for req in requirements:
            driver_value = metrics.get(req.requirement_type, 0)
            required_value = float(req.value)
            
            # Vérifier si l'exigence est remplie
            is_met = (
                (req.comparison_operator == '>=' and driver_value >= required_value) or
                (req.comparison_operator == '>' and driver_value > required_value) or
                (req.comparison_operator == '==' and driver_value == required_value)
            )
            
            if not is_met:
                all_requirements_met = False
            
            requirements_progress.append({
                'requirement_type': req.requirement_type,
                'description': req.description,
                'current_value': driver_value,
                'required_value': str(required_value),
                'comparison_operator': req.comparison_operator,
                'is_met': is_met
            })
        
        # Calculer la progression globale (pourcentage d'exigences remplies)
        if requirements:
            met_requirements = sum(1 for r in requirements_progress if r['is_met'])
            progress_percentage = int((met_requirements / len(requirements)) * 100)
        else:
            progress_percentage = 0
        
        # Sérialiser les objets Grade
        current_grade_serializer = GradeSerializer(current_grade.grade)
        next_grade_serializer = GradeSerializer(next_grade) if next_grade else None
        
        # Préparer les données de retour pour les tests
        return {
            'has_grade': True,
            # 'current_grade': current_grade.grade.name,
            'current_grade': current_grade_serializer.data,
            'next_grade': next_grade_serializer.data if next_grade_serializer else None,            
            # 'next_grade': {
            #     'name': next_grade.name,
            #     'commission_rate': float(next_grade.commission_rate),
            # },
            'metrics': metrics,
            'requirements': [
                {
                    'requirement_type': req.requirement_type,
                    'current_value': metrics.get(req.requirement_type, 0),
                    'required_value': str(req.value),
                    'comparison_operator': req.comparison_operator,
                    'is_met': (
                        (req.comparison_operator == '>=' and metrics.get(req.requirement_type, 0) >= float(req.value)) or
                        (req.comparison_operator == '>' and metrics.get(req.requirement_type, 0) > float(req.value)) or
                        (req.comparison_operator == '==' and metrics.get(req.requirement_type, 0) == float(req.value))
                    )
                }
                for req in requirements
            ],
            'progress': progress_percentage,
            'all_requirements_met': all_requirements_met
        }
    
    @classmethod
    def evaluate_and_update_driver_grade(cls, driver: Drivers) -> Tuple[bool, str]:
        """
        Évalue et met à jour le grade d'un chauffeur si nécessaire.
        
        Args:
            driver: Instance du chauffeur à évaluer
            
        Returns:
            Tuple (updated: bool, message: str)
        """
        # Calculer les métriques actuelles du chauffeur
        metrics = cls.evaluate_driver_metrics(driver)
        
        # Déterminer le grade approprié
        new_grade = cls.get_grade_for_metrics(metrics)
        
        if not new_grade:
            return False, "Aucun grade ne correspond aux critères actuels"
        
        # Mettre à jour le grade si nécessaire
        return cls.update_driver_grade(
            driver=driver,
            new_grade=new_grade,
            reason=f"Mise à jour automatique basée sur les performances: {metrics}"
        )
    
    @classmethod
    def bulk_update_drivers_grades(cls, driver_ids: List[str] = None) -> Dict:
        """
        Met à jour les grades de plusieurs chauffeurs en une seule opération.
        
        Args:
            driver_ids: Liste des IDs des chauffeurs à mettre à jour (tous si None)
            
        Returns:
            Dictionnaire avec les statistiques de mise à jour
        """
        result = {
            'total_processed': 0,
            'grades_updated': 0,
            'errors': [],
            'updated_drivers': []
        }
        
        # Récupérer tous les chauffeurs ou seulement ceux spécifiés
        query = Drivers.objects.all()
        if driver_ids:
            query = query.filter(id__in=driver_ids)
        
        for driver in query.iterator(chunk_size=100):
            try:
                updated, message = cls.evaluate_and_update_driver_grade(driver)
                result['total_processed'] += 1
                
                if updated:
                    result['grades_updated'] += 1
                    result['updated_drivers'].append({
                        'driver_id': str(driver.id),
                        'new_grade': driver.grades.filter(drivergrade__is_current=True).first().name,
                        'message': message
                    })
            except Exception as e:
                result['errors'].append({
                    'driver_id': str(driver.id) if driver else 'unknown',
                    'error': str(e)
                })
        
        return result
