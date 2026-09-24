import datetime
import math
from drivers.models import Drivers
from rides.models import *
from django.db.models import Avg
import re
from django.utils.timezone import now

class RidesEstimateamount:
    """Initializes the RidesEstimateamount object."""
    def __init__(self):
        pass

    def get_amount_by_prestation(self, distance_km):

        """
        Returns the base, per kilometer, and per minute rates based on the distance.

        Args:
            distance_km (float): The distance in kilometers.

        Returns:
            tuple: Three dictionaries containing the base, per kilometer, and per minute rates for each category.
        """
        if distance_km >= 19:
            base_fares = {"economy": 450, "comfort": 600, "prestige": 900}
            per_km_rates = {"economy": 60, "comfort": 80, "prestige": 110}
            per_min_rates = {"economy": 35, "comfort": 65, "prestige": 85}
        elif 10 <= distance_km < 19:
            base_fares = {"economy": 450, "comfort": 600, "prestige": 900}
            per_km_rates = {"economy": 40, "comfort": 60, "prestige": 80}
            per_min_rates = {"economy": 25, "comfort": 35, "prestige": 65}
        elif 5 <= distance_km < 10:
            base_fares = {"economy": 450, "comfort": 600, "prestige": 900}
            per_km_rates = {"economy": 30, "comfort": 40, "prestige": 50}
            per_min_rates = {"economy": 10, "comfort": 15, "prestige": 20}
        else:
            base_fares = {"economy": 450, "comfort": 600, "prestige": 900}
            per_km_rates = {"economy": 1, "comfort": 1, "prestige": 1}
            per_min_rates = {"economy": 1, "comfort": 1, "prestige": 1}

        return base_fares, per_km_rates, per_min_rates

    def calculate_dynamic_markup(self, distance_km, category):
        """
        Calculates the dynamic markup based on the distance and category.

        Args:
            distance_km (float): The distance in kilometers.
            category (str): The category of the ride ('economy', 'comfort', 'prestige').

        Returns:
            float: The dynamic markup.
        """

        if category == "economy":
            return max(300 - (distance_km * 10), 200)   
        elif category == "comfort":
            return max(500 - (distance_km * 15), 350)  
        else:
            return max(700 - (distance_km * 20), 500) 
        

    def get_time_based_multiplier(self, current_time: datetime) -> float:
        """
        Returns a multiplier based on the current time.

        Args:
            current_time (datetime): The current time.

        Returns:
            float: The time-based multiplier.
        """

        hour = current_time.hour

        if 5 <= hour < 11:     # Matin
            return 1.05
        elif 11 <= hour < 15:  # Midi
            return 1.10
        elif 15 <= hour < 18:  # Après-midi
            return 1.00
        elif 18 <= hour < 22:  # Soir
            return 1.15
        else:                  # Tard le soir
            return 1.20


    def estimate_fares(self, distance_km, duration_min, duration_in_traffic= None, congestion_info=True,  current_time=None):
        """
        Estimates the fares for a ride based on distance, duration, and other parameters.

        Args:
            distance_km (float): The distance in kilometers.
            duration_min (int): The duration in minutes.
            duration_in_traffic (int, optional): The duration in minutes considering traffic.
            congestion_info (bool, optional): Indicates if congestion information should be considered.
            current_time (datetime, optional): The current time. If not provided, the current time is used.

        Returns:
            dict: The estimated fares for each category.
        """

        if current_time is None:
            current_time = now()

        time_multiplier = self.get_time_based_multiplier(current_time)


        fares = {}
        base_fares, per_km_rates, per_min_rates = self.get_amount_by_prestation(distance_km)

        for category, base_fare in base_fares.items():
            per_km_rate = per_km_rates[category]
            per_min_rate = per_min_rates[category]
            dynamic_markup = self.calculate_dynamic_markup(distance_km, category)

            total_fare = (
                base_fare +
                (distance_km * per_km_rate) +
                (duration_min * per_min_rate) +
                dynamic_markup
            )

            total_fare = total_fare * time_multiplier


            if congestion_info and duration_in_traffic:

                delay_ratio = duration_in_traffic / duration_min if duration_min > 0 else 1
                traffic_markup = (delay_ratio - 1) * 0.2  
                total_fare *= (1 + min(traffic_markup, 0.2))  

            if congestion_info:
                total_fare += 300   

            fares[category] = round(math.ceil(total_fare) / 50) * 50

        return fares


    def parse_duration_to_minutes(self , duration_str):
        """
        Converts a duration string to minutes.

        Args:
            duration_str (str): The duration string (e.g., "1 hour 30 min").

        Returns:
            int: The total duration in minutes.
        """
        hours = 0
        minutes = 0

        hour_match = re.search(r"(\d+)\s*hour", duration_str)
        minute_match = re.search(r"(\d+)\s*min", duration_str)

        if hour_match:
            hours = int(hour_match.group(1))
        if minute_match:
            minutes = int(minute_match.group(1))

        total_minutes = hours * 60 + minutes
        return total_minutes

