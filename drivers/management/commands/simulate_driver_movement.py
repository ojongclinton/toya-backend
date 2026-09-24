from django.core.management.base import BaseCommand
import random
import time
from django.utils import timezone

class Command(BaseCommand):
    help = 'Simule le mouvement des chauffeurs en temps réel'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=10,
            help='Intervalle de mise à jour en secondes (défaut: 10)'
        )
        parser.add_argument(
            '--distance',
            type=float,
            default=0.005,
            help='Distance maximale de déplacement (défaut: 0.005 ≈ 500m)'
        )
        parser.add_argument(
            '--drivers',
            type=str,
            default='all',
            help='Filtre: "all", "test" (test_driver_*), ou IDs séparés par virgule (ex: 1,2,3)'
        )
    
    def handle(self, *args, **options):
        from drivers.models import Drivers
        from navigation.models import Position
        
        interval = options['interval']
        max_distance = options['distance']
        driver_filter = options['drivers']
        
        self.stdout.write(self.style.SUCCESS('🚗 Simulation du mouvement des chauffeurs...'))
        self.stdout.write(f'⏱️  Mise à jour toutes les {interval} secondes')
        self.stdout.write(f'📏 Distance max: ±{max_distance} (≈{int(max_distance*111000)}m)')
        self.stdout.write(self.style.WARNING('🛑 Ctrl+C pour arrêter\n'))
        
        try:
            iteration = 0
            while True:
                iteration += 1
                
                # Filtrer les chauffeurs selon l'option
                if driver_filter == 'test':
                    drivers = Drivers.objects.filter(
                        is_available=True,
                        username__startswith='test_driver_'
                    )
                elif driver_filter == 'all':
                    drivers = Drivers.objects.filter(is_available=True)
                else:
                    # IDs spécifiques
                    try:
                        ids = [int(x.strip()) for x in driver_filter.split(',')]
                        drivers = Drivers.objects.filter(
                            id__in=ids,
                            is_available=True
                        )
                    except ValueError:
                        self.stdout.write(self.style.ERROR(
                            f'❌ Format invalide pour --drivers: {driver_filter}'
                        ))
                        return
                
                if not drivers.exists():
                    self.stdout.write(self.style.WARNING(
                        '⚠️  Aucun chauffeur disponible trouvé'
                    ))
                    time.sleep(interval)
                    continue
                
                updated_count = 0
                
                for driver in drivers:
                    position = Position.objects.filter(user_id=driver).first()
                    
                    if position:
                        # Déplacement aléatoire
                        lat_change = random.uniform(-max_distance, max_distance)
                        lon_change = random.uniform(-max_distance, max_distance)
                        
                        position.lat += lat_change
                        position.lon += lon_change
                        position.timestamp = timezone.now()
                        position.save()
                        
                        self.stdout.write(
                            f'📍 {driver.first_name} ({driver.username}): '
                            f'({position.lat:.6f}, {position.lon:.6f})'
                        )
                        updated_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠️  Pas de position pour {driver.first_name}'
                            )
                        )
                
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Itération #{iteration}: {updated_count} positions mises à jour - '
                    f'{timezone.now().strftime("%H:%M:%S")}\n'
                ))
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n🛑 Simulation arrêtée'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur: {e}'))