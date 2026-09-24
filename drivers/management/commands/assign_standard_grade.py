from django.core.management.base import BaseCommand
from django.utils import timezone
from drivers.models import Drivers, Grade, DriverGrade

class Command(BaseCommand):
    help = 'Attribue le grade Standard à tous les chauffeurs qui n\'en ont pas encore'

    def handle(self, *args, **options):
        try:
            # Récupérer le grade Standard
            standard_grade = Grade.objects.get(name='Standard', is_active=True)
            
            # Récupérer les chauffeurs sans grade actif
            drivers_without_grade = Drivers.objects.exclude(
                grade_history__is_current=True
            ).distinct()
            
            total_drivers = drivers_without_grade.count()
            
            if total_drivers == 0:
                self.stdout.write(self.style.SUCCESS('Tous les chauffeurs ont déjà un grade actif.'))
                return
                
            self.stdout.write(f"Attribution du grade Standard à {total_drivers} chauffeurs...")
            
            # Attribuer le grade Standard à chaque chauffeur
            updated_count = 0
            for driver in drivers_without_grade.iterator():
                # Vérifier à nouveau pour éviter les doublons (au cas où)
                if not driver.grade_history.filter(is_current=True).exists():
                    DriverGrade.objects.create(
                        driver=driver,
                        grade=standard_grade,
                        is_current=True,
                        assigned_at=timezone.now(),
                        reason="Attribution rétroactive du grade Standard"
                    )
                    updated_count += 1
                    
                    # Afficher la progression
                    if updated_count % 100 == 0:
                        self.stdout.write(f"{updated_count} chauffeurs mis à jour...")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Terminé ! {updated_count} chauffeurs ont reçu le grade Standard.'
                )
            )
            
        except Grade.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("Le grade Standard n'existe pas. Veuillez d'abord exécuter la commande 'init_grades'.")
            )
