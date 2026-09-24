"""
Commande de gestion pour initialiser les grades par défaut dans la base de données.

Exemple d'utilisation :
    python manage.py init_grades
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from drivers.models import Grade, GradeRequirement


class Command(BaseCommand):
    help = 'Initialise les grades par défaut avec leurs exigences associées.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Début de l\'initialisation des grades...'))
        
        # Définition des grades par défaut
        default_grades = [
            {
                'name': 'Standard',
                'commission_rate': 15.00,
                'is_active': True,
                'requirements': [
                    # Aucune exigence pour le grade Standard (attribué par défaut)
                ]
            },
            {
                'name': 'Bronze',
                'commission_rate': 15.00,  # Même commission que Standard mais avec des avantages futurs
                'is_active': True,
                'requirements': [
                    {'type': GradeRequirement.RATING, 'operator': '>=', 'value': 4.0, 'description': 'Note moyenne minimale de 4.0/5'},
                    {'type': GradeRequirement.RIDES_COUNT, 'operator': '>=', 'value': 10, 'description': 'Minimum 50 courses effectuées'},
                    {'type': GradeRequirement.REFERRALS, 'operator': '>=', 'value': 2, 'description': 'Au moins 2 parrainages actifs'},
                ]
            },
            {
                'name': 'Silver',
                'commission_rate': 14.00,
                'is_active': True,
                'requirements': [
                    {'type': GradeRequirement.RATING, 'operator': '>=', 'value': 4.3, 'description': 'Note moyenne minimale de 4.3/5'},
                    {'type': GradeRequirement.RIDES_COUNT, 'operator': '>=', 'value': 200, 'description': 'Minimum 200 courses effectuées'},
                    {'type': GradeRequirement.REVENUE, 'operator': '>=', 'value': 15000, 'description': 'Chiffre d\'affaires minimum de 15 000 FCFA'},
                    {'type': GradeRequirement.REFERRALS, 'operator': '>=', 'value': 5, 'description': 'Au moins 5 parrainages actifs'},
                ]
            },
            {
                'name': 'Gold',
                'commission_rate': 13.00,
                'is_active': True,
                'requirements': [
                    {'type': GradeRequirement.RATING, 'operator': '>=', 'value': 4.5, 'description': 'Note moyenne minimale de 4.5/5'},
                    {'type': GradeRequirement.RIDES_COUNT, 'operator': '>=', 'value': 500, 'description': 'Minimum 500 courses effectuées'},
                    {'type': GradeRequirement.REVENUE, 'operator': '>=', 'value': 35000, 'description': 'Chiffre d\'affaires minimum de 35 000 FCFA'},
                    {'type': GradeRequirement.REFERRALS, 'operator': '>=', 'value': 10, 'description': 'Au moins 10 parrainages actifs'},
                ]
            },
            {
                'name': 'Platinum',
                'commission_rate': 12.00,
                'is_active': True,
                'requirements': [
                    {'type': GradeRequirement.RATING, 'operator': '>=', 'value': 4.8, 'description': 'Note moyenne minimale de 4.8/5'},
                    {'type': GradeRequirement.RIDES_COUNT, 'operator': '>=', 'value': 1000, 'description': 'Minimum 1 000 courses effectuées'},
                    {'type': GradeRequirement.REVENUE, 'operator': '>=', 'value': 50000, 'description': 'Chiffre d\'affaires minimum de 50 000 FCFA'},
                    {'type': GradeRequirement.REFERRALS, 'operator': '>=', 'value': 20, 'description': 'Au moins 20 parrainages actifs'},
                ]
            },
        ]

        with transaction.atomic():
            # Désactiver tous les grades existants (soft delete)
            Grade.objects.all().update(is_active=False)
            
            created_count = 0
            updated_count = 0
            
            for grade_data in default_grades:
                # Créer ou mettre à jour le grade
                grade, created = Grade.objects.update_or_create(
                    name=grade_data['name'],
                    defaults={
                        'commission_rate': grade_data['commission_rate'],
                        'is_active': grade_data['is_active']
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Création du grade : {grade.name}'))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Mise à jour du grade : {grade.name}'))
                
                # Supprimer les anciennes exigences
                grade.requirements.all().delete()
                
                # Ajouter les nouvelles exigences
                for req_data in grade_data['requirements']:
                    GradeRequirement.objects.create(
                        grade=grade,
                        requirement_type=req_data['type'],
                        comparison_operator=req_data['operator'],
                        value=req_data['value'],
                        description=req_data['description']
                    )
                    self.stdout.write(f'  - Ajout de l\'exigence : {req_data["description"]}')
            
            # Compter le nombre total de grades actifs
            total_grades = Grade.objects.filter(is_active=True).count()
            
            self.stdout.write(self.style.SUCCESS('\nRésumé de l\'initialisation :'))
            self.stdout.write(self.style.SUCCESS(f'- {created_count} nouveaux grades créés'))
            self.stdout.write(self.style.SUCCESS(f'- {updated_count} grades mis à jour'))
            self.stdout.write(self.style.SUCCESS(f'- {total_grades} grades actifs au total'))
            self.stdout.write(self.style.SUCCESS('\nInitialisation des grades terminée avec succès !'))
