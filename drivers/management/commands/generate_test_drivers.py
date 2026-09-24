from django.core.management.base import BaseCommand
import random
from decimal import Decimal
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Génère des chauffeurs de test avec positions autour de Douala'
    
    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=15)
        parser.add_argument('--clean', action='store_true', help='Supprimer les chauffeurs de test existants avant')
    
    def handle(self, *args, **options):
        from drivers.models import Drivers, Vehicle
        from navigation.models import Position
        
        count = options['count']
        
        # Nettoyage optionnel
        if options['clean']:
            deleted = Drivers.objects.filter(username__startswith='test_driver_').delete()
            self.stdout.write(f'🗑️  {deleted[0]} chauffeurs de test supprimés\n')
        
        douala_lat = 4.0511
        douala_lon = 9.7679
        
        brands_models = [
            ('Toyota', 'Corolla'), ('Honda', 'Civic'),
            ('Nissan', 'Sentra'), ('Hyundai', 'Elantra'),
            ('Kia', 'Rio'), ('Mazda', '3'),
        ]
        
        prestations = ['economy', 'confort', 'prestige']
        colors = ['white', 'purple']
        
        self.stdout.write(f'🚗 Génération de {count} chauffeurs...\n')
        
        # Trouver le prochain ID disponible
        existing_drivers = Drivers.objects.filter(
            username__startswith='test_driver_'
        ).values_list('username', flat=True)
        
        existing_ids = set()
        for username in existing_drivers:
            try:
                num = int(username.replace('test_driver_', ''))
                existing_ids.add(num)
            except ValueError:
                pass
        
        created_count = 0
        skipped_count = 0
        
        i = 1
        while created_count < count:
            # Trouver le prochain ID libre
            while i in existing_ids:
                i += 1
            
            phone = f'+23769{7000000 + i}'
            
            try:
                driver, created = Drivers.objects.get_or_create(
                    phone_number=phone,
                    defaults={
                        'username': f'test_driver_{i}',
                        'email': f'test_driver_{i}@test.com',
                        'first_name': f'Driver{i}',
                        'last_name': 'Test',
                        'adresse': 'Douala, Cameroun',
                        'is_available': True,
                        'is_phone_verified': True,
                        'wallet_money': Decimal('5000.00')
                    }
                )
                
                if created:
                    driver.set_password('test1234')
                    driver.save()
                    
                    brand, model = random.choice(brands_models)
                    
                    # Vérifier si véhicule existe déjà
                    if not Vehicle.objects.filter(driver_id=driver).exists():
                        Vehicle.objects.create(
                            driver_id=driver,
                            vehicle_brand=brand,
                            vehicle_model=model,
                            vehicle_color=random.choice(colors),
                            license_plate=f'TEST-{i:03d}-DL',
                            prestation=random.choice(prestations),
                            validation_status='validated'
                        )
                    
                    # Vérifier si position existe déjà
                    if not Position.objects.filter(user_id=driver).exists():
                        Position.objects.create(
                            user_id=driver,
                            lat=douala_lat + random.uniform(-0.09, 0.09),
                            lon=douala_lon + random.uniform(-0.09, 0.09),
                            address=f'Zone Test {i}, Douala'
                        )
                    
                    self.stdout.write(f'✅ Chauffeur {i}: {driver.first_name} ({brand} {model})')
                    created_count += 1
                else:
                    self.stdout.write(f'⏭️  Chauffeur {i} existe déjà, skip...')
                    skipped_count += 1
                
                existing_ids.add(i)
                i += 1
                
            except IntegrityError as e:
                self.stdout.write(f'⚠️  Erreur pour chauffeur {i}: {str(e)[:100]}')
                i += 1
                continue
        
        self.stdout.write(self.style.SUCCESS(
            f'\n🎉 Terminé! {created_count} créés, {skipped_count} déjà existants. Mot de passe: test1234'
        ))