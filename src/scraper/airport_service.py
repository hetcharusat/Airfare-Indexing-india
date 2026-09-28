import os
import json
import math
from typing import Dict, Any, Optional, List

class AirportService:
    """
    Service for querying airport metadata, coordinates, and distances
    loaded from airport-code.json.
    """
    def __init__(self, airport_file_path: Optional[str] = None):
        if not airport_file_path:
            # Look in workspace root
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            airport_file_path = os.path.join(base_dir, "airport-code.json")
        
        self.airport_map: Dict[str, Dict[str, Any]] = {}
        self.indian_airports: Dict[str, Dict[str, Any]] = {}
        self._load_airports(airport_file_path)

    def _load_airports(self, path: str):
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            airports = data.get("responsePayload", {}).get("data", [])
            for a in airports:
                code = a.get("airportCode", "").upper()
                if code:
                    self.airport_map[code] = a
                    if a.get("countryCode") == "IN":
                        self.indian_airports[code] = a
        except Exception as e:
            print(f"[AirportService] Warning loading {path}: {e}")

    def get_airport(self, code: str) -> Optional[Dict[str, Any]]:
        return self.airport_map.get(code.upper())

    def get_city_name(self, code: str) -> str:
        airport = self.get_airport(code)
        if airport:
            return airport.get("airportCity", code)
        return code

    def calculate_distance_km(self, origin: str, destination: str) -> Optional[float]:
        """Calculates Great-Circle (Haversine) distance between two airports in km."""
        a1 = self.get_airport(origin)
        a2 = self.get_airport(destination)
        if not a1 or not a2:
            return None
        
        lat1, lon1 = a1.get("latitude"), a1.get("longitude")
        lat2, lon2 = a2.get("latitude"), a2.get("longitude")
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return None

        R = 6371.0  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 1)

airport_service = AirportService()
