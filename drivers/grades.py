from drivers.models import Drivers
from rides.models import ReviewRating, Rides
from django.db.models import Avg, Sum, Count
from datetime import datetime
from django.db.models.functions import TruncDate
from referrals.models import ReferralsClient, ReferralsDrivers 

class DriverGrade:
    def __init__(self, driver_id) -> None: 
        self.driver_id = driver_id
        self.grades_thresholds = {
            'Standard': {
                'rating': 1,
                'reviews': 1,
                'total_count_rides': 1,
                'revenue': 10000,
                "referrals_count": 0
            },
            'Bronze': {
                'rating': 4,
                'reviews': 20,
                'total_count_rides': 100,
                'revenue': 750000,
                "referrals_count": 2
            },
            'Silver': {
                'rating': 4,
                'reviews': 50,
                'total_count_rides': 300,
                'revenue': 2000000,
                "referrals_count": 2
            },
            'Gold': {
                'rating': 4,
                'reviews': 100,
                'total_count_rides': 500,
                'revenue': 4000000,
                "referrals_count": 3
            },
            'Platinum': {
                'rating': 4,
                'reviews': 100,
                'total_count_rides': 700,
                'revenue': 6000000,
                "referrals_count": 4
            },
        }

    def count_total_rides(self, number):
        rides_by_driver = Rides.objects.filter(driver_id=self.driver_id)
        rides_count = rides_by_driver.count() or 0
        tmp_content_rides_count = rides_count >= number
        return tmp_content_rides_count, rides_count

    def calculate_grade_driver(self):
        driver = Drivers.objects.get(id=self.driver_id)
        
        referrals_count = ReferralsDrivers.objects.filter(referrer_driver_id=driver).count() or 0
        all_review_rating = ReviewRating.objects.filter(driver_id=driver)
        mean_of_all_review_rating = all_review_rating.aggregate(Avg('rating'))['rating__avg'] or 0
        total_of_comment = all_review_rating.count() or 0
        all_rides_by_drivers = Rides.objects.filter(driver_id=driver)
        sum_gain_all_rides_by_drivers = all_rides_by_drivers.aggregate(Sum('final_price'))['final_price__sum'] or 0
        
        all_informations = {
            "rating": mean_of_all_review_rating,
            "reviews": total_of_comment,
            "referrals_count": referrals_count,
            "revenue": sum_gain_all_rides_by_drivers,
        }
        
        return all_informations

    def get_grade_for_a_driver(self):
        all_informations = self.calculate_grade_driver()
        
        # CALCULER total_count_rides UNE SEULE FOIS
        _, total_rides = self.count_total_rides(0)
        
        # Platinum
        if (all_informations['rating'] >= 4 and 
            all_informations['reviews'] >= 100 and 
            total_rides >= 700 and 
            all_informations['revenue'] >= 6000000 and 
            all_informations['referrals_count'] >= 4):
            all_informations['total_count_rides'] = total_rides  
            all_informations['grade'] = 'Platinum'
            return all_informations, 17
        
        # Gold
        elif (all_informations['rating'] >= 4 and 
              all_informations['reviews'] >= 100 and 
              total_rides >= 500 and 
              all_informations['revenue'] >= 4000000 and 
              all_informations['referrals_count'] >= 3):
            all_informations['total_count_rides'] = total_rides  
            all_informations['grade'] = 'Gold'
            return all_informations, 18
        
        # Silver
        elif (all_informations['rating'] >= 4 and 
              all_informations['reviews'] >= 50 and 
              total_rides >= 300 and 
              all_informations['revenue'] >= 2000000 and 
              all_informations['referrals_count'] >= 2):
            all_informations['total_count_rides'] = total_rides
            return all_informations, 19
        
        # Bronze
        elif (all_informations['rating'] >= 4 and 
              all_informations['reviews'] >= 20 and 
              total_rides >= 100 and 
              all_informations['revenue'] >= 750000 and 
              all_informations['referrals_count'] >= 2):
            all_informations['total_count_rides'] = total_rides  
            all_informations['grade'] = 'Bronze'
            return all_informations, 20
        
        # Standard (défaut)
        else:
            all_informations['total_count_rides'] = total_rides  
            all_informations['grade'] = 'Standard'
            return all_informations, 20

    def get_evolution_to_next_grade(self):
        all_informations, _ = self.get_grade_for_a_driver()
        
        current_grade = all_informations['grade']
        current_grade_data = self.grades_thresholds[current_grade]
        current_grade_index = list(self.grades_thresholds).index(current_grade)
        
        grades_list = list(self.grades_thresholds.items())
        
        if current_grade_index < len(grades_list) - 1:
            next_grade, next_grade_data = grades_list[current_grade_index + 1]
            
            _, total_rides = self.count_total_rides(0)
            
            evolution_grade = {
                'rating': all_informations['rating'] >= next_grade_data['rating'],
                'reviews': all_informations['reviews'] >= next_grade_data['reviews'],
                'total_count_rides': total_rides >= next_grade_data['total_count_rides'],  
                'revenue': all_informations['revenue'] >= next_grade_data['revenue'],
                "referrals_count": all_informations['referrals_count'] >= next_grade_data['referrals_count'],
            }
            
            # NOUVEAU: Calculer progression détaillée pour chaque critère
            detailed_progress = {
                'rating': {
                    'current': round(all_informations['rating'], 1),
                    'required': next_grade_data['rating'],
                    'percentage': min(100, round((all_informations['rating'] / next_grade_data['rating']) * 100, 1)),
                    'achieved': evolution_grade['rating']
                },
                'reviews': {
                    'current': all_informations['reviews'],
                    'required': next_grade_data['reviews'],
                    'percentage': min(100, round((all_informations['reviews'] / next_grade_data['reviews']) * 100, 1)),
                    'achieved': evolution_grade['reviews']
                },
                'total_count_rides': {
                    'current': total_rides,
                    'required': next_grade_data['total_count_rides'],
                    'percentage': min(100, round((total_rides / next_grade_data['total_count_rides']) * 100, 1)),
                    'achieved': evolution_grade['total_count_rides']
                },
                'revenue': {
                    'current': all_informations['revenue'],
                    'required': next_grade_data['revenue'],
                    'percentage': min(100, round((all_informations['revenue'] / next_grade_data['revenue']) * 100, 1)),
                    'achieved': evolution_grade['revenue']
                },
                'referrals_count': {
                    'current': all_informations['referrals_count'],
                    'required': next_grade_data['referrals_count'],
                    'percentage': min(100, round((all_informations['referrals_count'] / max(1, next_grade_data['referrals_count'])) * 100, 1)) if next_grade_data['referrals_count'] > 0 else 100,
                    'achieved': evolution_grade['referrals_count']
                }
            }
            
            percentage_to_next_grade = self.calculate_percentage_to_next_grade(evolution=evolution_grade)
            
            result = {
                "Current Position": {
                    "percentage_to_next_grade": percentage_to_next_grade,
                    "detailed_progress": detailed_progress,  # ← NOUVEAU
                    "Data": all_informations
                },
                "Next Position": {
                    "percentage_remaining_to_next_grade": (100 - percentage_to_next_grade),
                    "grade": next_grade,
                    "Data": next_grade_data
                },
            }
        else:
            result = {
                "Current Position": {
                    "percentage_to_next_grade": 100,
                    "Data": all_informations
                },
                "Next Position": {
                    "percentage_remaining_to_next_grade": 0,
                    "Data": "Vous êtes déjà au dernier grade."
                },
            }
        
        return result

    def calculate_percentage_to_next_grade(self, evolution):
        total_items = len(evolution)
        true_count = sum(1 for value in evolution.values() if value is True)
        
        if total_items > 0:
            true_percentage = (true_count / total_items) * 100
        else:
            true_percentage = 0
        
        return true_percentage