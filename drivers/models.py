from django.db import models
from uuid import uuid4
from core.models import BaseUser
import random 
import string
import os 
from django.utils.timezone import now
from django.utils import timezone
from django.db import transaction
from decimal import Decimal


def vehicule_directory_path(instance , filename):
    
    return f"user/drivers/{str(instance.id)}/{filename}" 

# TODO - FIXME -> For some reasons that I don't know, when ever I trigger migrations it suggests I altered the profile_photo of the driver model despite not doing the change. Please investigate the issue, it is minor but all issues related to migrations are NEVER Fun to deal with. In this sense, NEVER update the docker compose file to automatically include makemigrations and migrate instructions as the level of confusion and breakage this will create will be too much to handle. 

class Drivers(BaseUser): 
    username        = models.CharField(max_length=255, null=False)
    first_name      = models.CharField(max_length=255, null=False)
    last_name       = models.CharField(max_length=255, null=False)
    phone_number    = models.CharField(max_length=15, null=False, unique=True)
    adresse         = models.CharField(max_length=255, null=True)
    referral_code   = models.CharField(max_length=20, null=True ,unique=True , default=None)
    wallet_money    = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Driver wallet balance in FCFA"
    )
    is_available    = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to=vehicule_directory_path, null=True, blank=True) 
    is_phone_verified = models.BooleanField(default=False, help_text="Whether the user's phone number has been verified via OTP")

    # grade_level     = models.CharField(max_length= 255 , default=)

    def save(self, *args, **kwargs):
        # Générer le code de parrainage si nécessaire
        if not self.referral_code:
            self.referral_code = self.genereate_unique_referral_code()
            
        # Sauvegarder d'abord l'instance pour obtenir un ID
        is_new = self._state.adding
        super(Drivers, self).save(*args, **kwargs)
        
        # Si c'est une nouvelle instance, attribuer le grade Standard
        if is_new:
            self._assign_default_grade()
    
    def _assign_default_grade(self):
        """Attribue automatiquement le grade Standard à un nouveau chauffeur."""
        from django.utils import timezone
        
        # Récupérer le grade Standard
        try:
            standard_grade = Grade.objects.get(name='Standard', is_active=True)
            
            # Vérifier si le chauffeur a déjà un grade actif
            has_active_grade = self.grade_history.filter(is_current=True).exists()
            
            if not has_active_grade:
                # Créer une nouvelle entrée dans l'historique des grades
                DriverGrade.objects.create(
                    driver=self,
                    grade=standard_grade,
                    is_current=True,
                    assigned_at=timezone.now(),
                    reason="Attribution automatique du grade Standard à la création du compte"
                )
        except Grade.DoesNotExist:
            # Si le grade Standard n'existe pas, on ne fait rien (peut-être logger une erreur)
            pass
        
    def genereate_unique_referral_code(self): 
        while True : 
            name = self.first_name.replace(' ', '_')
            reste = 16 - len(name)
            code = f'{name}'.upper() + ''.join(random.choices(string.ascii_uppercase + string.digits, k=reste))
            if not Drivers.objects.filter(referral_code=code).exists() : 
                return code 
        
    
    def __str__(self):
        return str(self.id)
    
        
    

    


def vehicule_directory_path(instance , filename):
    
    return f"vehicule/{str(instance.driver_id)}/{filename}" 
    

class Vehicle(models.Model) : 
    TYPE_OF_PRESTATION = [
        ("economy", "Economy"), 
        ("confort", "Confort"),
        ("prestige", "Prestige")
    ]
    
     # Choix de couleurs prédéfinies
    VEHICLE_COLORS = [
        ('white', 'Blanc'),
        ('black', 'Noir'),
        ('gray', 'Gris'),
        ('silver', 'Argent'),
        ('blue', 'Bleu'),
        ('red', 'Rouge'),
        ('green', 'Vert'),
        ('yellow', 'Jaune'),
        ('brown', 'Marron'),
        ('orange', 'Orange'),
        ('purple', 'Violet'),
        ('other', 'Autre'),
    ]
    
    id                          = models.UUIDField(primary_key=True , unique=True,  default=uuid4 , null=False)
    driver_id                   = models.OneToOneField("drivers.drivers" , on_delete= models.CASCADE)  
    vehicle_brand               = models.CharField(max_length=50,   null=False,  default='Not specified',  help_text="Marque du véhicule (ex: Toyota, Honda, Mercedes)" )
    vehicle_model               = models.CharField(max_length=50,   null=False,  default='Not specified',  help_text="Modèle du véhicule (ex: Corolla, Civic, C-Class)" )
    vehicle_color               = models.CharField( max_length=20,  choices=VEHICLE_COLORS, default='purple', null=False,help_text="Couleur principale du véhicule")
    license_plate               = models.CharField(max_length=20, unique=True , null=False,  default='Not specified')
    prestation                  = models.CharField(max_length=255, choices=TYPE_OF_PRESTATION, default='economy', null=False, help_text="Type of service this vehicle provides")
    technical_inspection_date   = models.DateField(null=True, blank=True) 
    photos                      = models.ImageField(upload_to=vehicule_directory_path, blank=True , null=False) 
    vehicle_rental_contract     = models.ImageField(upload_to=vehicule_directory_path, blank=True , null=False) 
    driving_licence_front       = models.ImageField(upload_to=vehicule_directory_path, blank=True , null=False) 
    driving_licence_back        = models.ImageField(upload_to=vehicule_directory_path, blank=True , null=False) 
    insurrance_file             = models.ImageField(upload_to=vehicule_directory_path, blank=True , null=False)
    criminal_record_certificate = models.FileField(upload_to=vehicule_directory_path, blank=True, null=True, help_text="Criminal record certificate (required for prestige vehicles) - Accepts PDF, images, and other document formats")
    technical_control_document  = models.FileField(upload_to=vehicule_directory_path, blank=True, null=True, help_text="Technical control document (required for prestige vehicles) - Accepts PDF, images, and other document formats")
    #  Dates d'expiration
    technical_control_expiry_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date d'expiration de la visite technique"
    )
    insurance_expiry_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date d'expiration de l'assurance"
    )
    driving_licence_expiry_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date d'expiration du permis de conduire"
    )
    criminal_record_expiry_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date d'expiration du casier judiciaire (généralement 3 mois)"
    )
    
    #  Dates de validation par admin
    technical_control_validated_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date de validation de la visite technique par l'admin"
    )
    insurance_validated_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date de validation de l'assurance par l'admin"
    )
    driving_licence_validated_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date de validation du permis par l'admin"
    )
    criminal_record_validated_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date de validation du casier judiciaire par l'admin"
    )
    
    validation_status           = models.CharField(max_length=255 ,default="in pending" ,  choices=[("in pending", "In pending"),("rejected", "Rejected"), ("validated", "Validated"),  ])
    uploaded_at                 = models.DateTimeField(auto_now_add=True)
    

    
    def __str__(self): 
        return str(self.id)



class Subscription(models.Model):
    id                          = models.UUIDField(primary_key=True , unique=True,  default=uuid4 , null=False)
    driver_id                   = models.OneToOneField("drivers.drivers" , on_delete= models.CASCADE)  
    start_date                  = models.DateTimeField(auto_now_add=True)  
    end_date                    = models.DateTimeField()  
    active                      = models.BooleanField(default=True)  
    created_at                  = models.DateTimeField(auto_now_add=True)  
    updated_at                  = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return str(self.id)

    def is_active(self):
        return self.active and self.end_date >= timezone.now()


class Grade(models.Model):
    """
    Représente un niveau de grade pour les chauffeurs.
    Les grades déterminent le pourcentage de commission appliqué aux courses.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Nom du grade (ex: Standard, Bronze, Silver, Gold, Platinum)"
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Taux de commission en pourcentage (ex: 20.00 pour 20%)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indique si ce grade est actuellement utilisé"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['commission_rate']  # Ordonne par taux de commission croissant
        verbose_name = "Grade"
        verbose_name_plural = "Grades"

    def __str__(self):
        return f"{self.name}"
        # return f"{self.name} ({self.commission_rate}%)"


class GradeRequirement(models.Model):
    """
    Définit les exigences nécessaires pour atteindre un grade spécifique.
    Un grade peut avoir plusieurs exigences (ex: note minimale, nombre de courses, etc.)
    """
    # Types d'exigences possibles
    RATING = 'rating'
    RIDES_COUNT = 'rides_count'
    REVENUE = 'revenue'
    REFERRALS = 'referrals'
    
    REQUIREMENT_TYPES = [
        (RATING, 'Note moyenne minimale'),
        (RIDES_COUNT, 'Nombre minimum de courses'),
        (REVENUE, 'Chiffre d\'affaires minimum'),
        (REFERRALS, 'Nombre minimum de parrainages'),
    ]
    
    # Opérateurs de comparaison
    GREATER_THAN_OR_EQUAL = '>='
    GREATER_THAN = '>'
    EQUAL = '=='
    
    COMPARISON_OPERATORS = [
        (GREATER_THAN_OR_EQUAL, 'Supérieur ou égal à'),
        (GREATER_THAN, 'Supérieur à'),
        (EQUAL, 'Égal à'),
    ]
    
    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE,
        related_name='requirements',
        help_text="Grade associé à cette exigence"
    )
    requirement_type = models.CharField(
        max_length=20,
        choices=REQUIREMENT_TYPES,
        help_text="Type d'exigence (note, nombre de courses, etc.)"
    )
    comparison_operator = models.CharField(
        max_length=2,
        choices=COMPARISON_OPERATORS,
        default=GREATER_THAN_OR_EQUAL,
        help_text="Opérateur de comparaison pour évaluer l'exigence"
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valeur seuil à atteindre pour satisfaire l'exigence"
    )
    description = models.TextField(
        blank=True,
        help_text="Description conviviale de l'exigence (optionnel)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Exigence de grade"
        verbose_name_plural = "Exigences de grade"
        ordering = ['grade__commission_rate', 'requirement_type']
        unique_together = ['grade', 'requirement_type']

    def __str__(self):
        return f"{self.grade.name}: {self.get_requirement_type_display()} {self.comparison_operator} {self.value}"


class DriverGrade(models.Model):
    """
    Modèle à travers pour la relation M2M entre Drivers et Grade.
    Permet de suivre l'historique des grades d'un chauffeur.
    """
    driver = models.ForeignKey(
        'Drivers',
        on_delete=models.CASCADE,
        related_name='grade_history',
        help_text="Chauffeur associé à ce grade"
    )
    grade = models.ForeignKey(
        'Grade',
        on_delete=models.CASCADE,
        related_name='driver_assignments',
        help_text="Grade attribué au chauffeur"
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date et heure d'attribution du grade"
    )
    unassigned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date et heure de fin de validité du grade (si le grade a été retiré)"
    )
    is_current = models.BooleanField(
        default=True,
        help_text="Indique si c'est le grade actuel du chauffeur"
    )
    reason = models.TextField(
        blank=True,
        null=True,
        help_text="Raison de l'attribution ou du retrait du grade (optionnel)"
    )

    class Meta:
        verbose_name = "Grade du chauffeur"
        verbose_name_plural = "Grades des chauffeurs"
        ordering = ['-assigned_at']
        constraints = [
            models.UniqueConstraint(
                fields=['driver'],
                condition=models.Q(is_current=True),
                name='unique_current_grade_per_driver'
            )
        ]

    def save(self, *args, **kwargs):
        # S'assurer qu'un seul grade est marqué comme actif par chauffeur
        if self.is_current:
            DriverGrade.objects.filter(
                driver=self.driver,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        
        # Si unassigned_at est défini, le grade n'est plus actif
        if self.unassigned_at is not None and self.is_current:
            self.is_current = False
            
        super().save(*args, **kwargs)

    def __str__(self):
        status = "actuel" if self.is_current else "historique"
        return f"{self.driver.id} - {self.grade.name} ({status} depuis {self.assigned_at.date()})"


# Mise à jour du modèle Drivers pour inclure la relation M2M avec Grade via DriverGrade
Drivers.add_to_class('grades', models.ManyToManyField(
    'Grade',
    through='DriverGrade',
    through_fields=('driver', 'grade'),
    related_name='drivers',
    help_text="Grades associés à ce chauffeur (historique et actuel)"
))
