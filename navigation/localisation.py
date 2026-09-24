import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GMAPS_TIMEOUT = 10


class GoogleMaps:
    def __init__(self) -> None:
        pass

    def calcul_distance_beetween_localisation(self, rides_source, driver_source, all_data=False, language='fr'):
        if not GOOGLE_API_KEY:
            raise ValueError("Google Maps API key not found.")

        origin = f"{rides_source[0]},{rides_source[1]}"
        destination = f"{driver_source[0]},{driver_source[1]}"
        departure_time = int(datetime.now().timestamp())

        params = {
            "origin": origin,
            "destination": destination,
            "departure_time": departure_time,
            "traffic_model": "best_guess",
            "language": language,
            "key": GOOGLE_API_KEY,
        }

        try:
            response = requests.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params=params,
                timeout=GMAPS_TIMEOUT
            )
            data = response.json()
        except requests.exceptions.Timeout:
            print(f"[GoogleMaps] Timeout after {GMAPS_TIMEOUT}s for {origin} → {destination}")
            return None
        except Exception as e:
            print(f"[GoogleMaps] Error: {e}")
            return None

        if data.get("status") != "OK" or not data.get("routes"):
            print(f"[GoogleMaps] API status: {data.get('status')} for {origin} → {destination}")
            return None

        leg = data["routes"][0]["legs"][0]
        duration = leg["duration"]["text"]
        distance_text = leg["distance"]["text"]

        parts = distance_text.strip().split()
        value = float(parts[0].replace(",", "."))
        unit = parts[1].lower()
        distance_km = value / 1000 if unit.startswith("m") else value

        duration_in_traffic = leg.get("duration_in_traffic", {}).get("text", None)
        congestion_info = bool(duration_in_traffic and duration_in_traffic != duration)

        return {
            "distance": round(distance_km, 2),
            "duration": duration,
            "duration_in_traffic": duration_in_traffic,
            "congestion_info": congestion_info,
            "raw_data": data["routes"] if all_data else [],
        }

    def name_of_location_to_coordinate(self, name_of_location):
        if not GOOGLE_API_KEY:
            raise ValueError("Google Maps API key not found.")

        try:
            response = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": name_of_location, "key": GOOGLE_API_KEY},
                timeout=GMAPS_TIMEOUT
            )
            data = response.json()
        except Exception as e:
            print(f"[GoogleMaps] Geocode error: {e}")
            return None

        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]

        return None