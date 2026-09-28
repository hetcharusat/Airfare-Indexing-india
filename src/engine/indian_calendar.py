"""
Project APIx: Indian Cultural, Festival & Gazetted Holiday Calendar Engine (2026-2027)
Specification Chapter 3.2 & MoSPI Econometric Seasonal Calibration.

Provides comprehensive astronomical, national, and cultural festival tracking
across Indian domestic aviation corridors to isolate seasonal demand shocks
from core airfare price inflation.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Comprehensive 2026 & 2027 Indian Gazetted Holidays, Festivals & Pilgrimages
INDIAN_HOLIDAYS_CATALOG = [
    # --- 2026 CALENDAR ---
    {
        "id": "NY2026",
        "name": "New Year Domestic Travel Peak",
        "date": "2026-01-01",
        "window_start": "2025-12-25",
        "window_end": "2026-01-04",
        "category": "Leisure Peak",
        "national_surge_multiplier": 2.2,
        "affected_corridors": ["BOM-GOI", "DEL-GOI", "BLR-COK", "DEL-IXB", "DEL-SXR"],
        "cultural_context": "Annual winter holiday season across coastal and hill leisure destinations."
    },
    {
        "id": "MAK2026",
        "name": "Makar Sankranti / Pongal / Magh Bihu",
        "date": "2026-01-14",
        "window_start": "2026-01-12",
        "window_end": "2026-01-17",
        "category": "Harvest Festival",
        "national_surge_multiplier": 1.7,
        "affected_corridors": ["DEL-MAA", "BOM-MAA", "BLR-MAA", "BOM-HYD", "DEL-GAU"],
        "cultural_context": "Southern and Eastern harvest celebration; massive diaspora return to Tamil Nadu, Andhra, Assam."
    },
    {
        "id": "AYJ2026",
        "name": "Ayodhya Ram Mandir Annual Festival / Magh Mela",
        "date": "2026-01-22",
        "window_start": "2026-01-20",
        "window_end": "2026-01-25",
        "category": "Religious Pilgrimage",
        "national_surge_multiplier": 2.4,
        "affected_corridors": ["DEL-AYJ", "BOM-AYJ", "BLR-AYJ", "CCU-AYJ"],
        "cultural_context": "Consecration anniversary and winter pilgrimage rush to Ayodhya Dham."
    },
    {
        "id": "REP2026",
        "name": "Republic Day Long Weekend",
        "date": "2026-01-26",
        "window_start": "2026-01-23",
        "window_end": "2026-01-27",
        "category": "Gazetted Long Weekend",
        "national_surge_multiplier": 1.6,
        "affected_corridors": ["DEL-BOM", "BOM-GOI", "DEL-DED", "BLR-GOI"],
        "cultural_context": "National holiday 3-day weekend; high short-haul domestic getaway volumes."
    },
    {
        "id": "MSH2026",
        "name": "Maha Shivratri",
        "date": "2026-02-15",
        "window_start": "2026-02-13",
        "window_end": "2026-02-17",
        "category": "Religious Observance",
        "national_surge_multiplier": 1.5,
        "affected_corridors": ["DEL-VNS", "BOM-VNS", "DEL-DED"],
        "cultural_context": "Pilgrimage to Varanasi, Ujjain, Rishikesh, and Jyotirlinga shrines."
    },
    {
        "id": "HOL2026",
        "name": "Holi / Dhulandi Festival of Colours",
        "date": "2026-03-04",
        "window_start": "2026-03-01",
        "window_end": "2026-03-06",
        "category": "Major Cultural Festival",
        "national_surge_multiplier": 2.1,
        "affected_corridors": ["BOM-DEL", "BLR-DEL", "BOM-PAT", "DEL-JAI", "PNQ-DEL"],
        "cultural_context": "Nationwide spring homecoming across Northern and Western India."
    },
    {
        "id": "EID2026",
        "name": "Eid-ul-Fitr (Shawwal 1447)",
        "date": "2026-03-20",
        "window_start": "2026-03-18",
        "window_end": "2026-03-23",
        "category": "Gazetted Festival",
        "national_surge_multiplier": 1.9,
        "affected_corridors": ["DEL-HYD", "BOM-CCU", "DEL-SXR", "BLR-CCU", "BOM-LKO"],
        "cultural_context": "Culmination of Ramadan; heavy domestic family reunion traffic across urban hubs."
    },
    {
        "id": "EAD2026",
        "name": "Eid-ul-Adha (Bakrid 1447)",
        "date": "2026-05-27",
        "window_start": "2026-05-25",
        "window_end": "2026-05-30",
        "category": "Gazetted Festival",
        "national_surge_multiplier": 1.8,
        "affected_corridors": ["DEL-HYD", "BOM-HYD", "DEL-SXR", "BOM-COK"],
        "cultural_context": "Feast of Sacrifice; significant family and regional homecoming movement."
    },
    {
        "id": "IND2026",
        "name": "Independence Day Long Weekend",
        "date": "2026-08-15",
        "window_start": "2026-08-14",
        "window_end": "2026-08-17",
        "category": "Gazetted Long Weekend",
        "national_surge_multiplier": 1.7,
        "affected_corridors": ["DEL-GOI", "BOM-GOI", "DEL-DED", "BLR-IXG"],
        "cultural_context": "National holiday travel weekend connecting metros to leisure destinations."
    },
    {
        "id": "RAK2026",
        "name": "Raksha Bandhan",
        "date": "2026-08-28",
        "window_start": "2026-08-27",
        "window_end": "2026-08-30",
        "category": "Cultural Festival",
        "national_surge_multiplier": 1.6,
        "affected_corridors": ["BOM-DEL", "BLR-DEL", "PNQ-DEL", "DEL-BOM"],
        "cultural_context": "Sibling reunion festival creating sharp 48-hour return flight surges."
    },
    {
        "id": "ONM2026",
        "name": "Onam / Thiru Onam",
        "date": "2026-08-26",
        "window_start": "2026-08-23",
        "window_end": "2026-08-29",
        "category": "Harvest Festival",
        "national_surge_multiplier": 2.0,
        "affected_corridors": ["DEL-COK", "BOM-COK", "BLR-COK", "DEL-TRV", "BOM-TRV"],
        "cultural_context": "Kerala state festival; Malayali diaspora returns from Delhi, Mumbai, Bengaluru."
    },
    {
        "id": "GAN2026",
        "name": "Ganesh Chaturthi / Visarjan",
        "date": "2026-09-14",
        "window_start": "2026-09-13",
        "window_end": "2026-09-24",
        "category": "Cultural Festival",
        "national_surge_multiplier": 1.8,
        "affected_corridors": ["DEL-BOM", "BLR-BOM", "DEL-PNQ", "BLR-PNQ"],
        "cultural_context": "Western India festival centered in Mumbai and Pune; intense inter-city transit."
    },
    {
        "id": "NAV2026",
        "name": "Durga Puja / Navratri / Dussehra",
        "date": "2026-10-20",
        "window_start": "2026-10-16",
        "window_end": "2026-10-23",
        "category": "Major Cultural Festival",
        "national_surge_multiplier": 2.6,
        "affected_corridors": ["DEL-CCU", "BOM-CCU", "BLR-CCU", "HYD-CCU", "BOM-AMD"],
        "cultural_context": "Peak cultural celebration in West Bengal and Gujarat; massive diaspora return to Kolkata."
    },
    {
        "id": "DIW2026",
        "name": "Diwali / Deepavali & Dhanteras",
        "date": "2026-11-08",
        "window_start": "2026-11-04",
        "window_end": "2026-11-12",
        "category": "Super-Peak National Festival",
        "national_surge_multiplier": 3.1,
        "affected_corridors": ["BOM-DEL", "DEL-BOM", "DEL-PAT", "BOM-PAT", "BLR-DEL", "BOM-CCU"],
        "cultural_context": "Biggest festival in India. Pan-India domestic air travel surge with fares jumping 150-250%."
    },
    {
        "id": "CHT2026",
        "name": "Chhath Puja",
        "date": "2026-11-15",
        "window_start": "2026-11-13",
        "window_end": "2026-11-17",
        "category": "Major Cultural Festival",
        "national_surge_multiplier": 2.9,
        "affected_corridors": ["DEL-PAT", "BOM-PAT", "BLR-PAT", "CCU-PAT", "DEL-IXR"],
        "cultural_context": "Sacred solar festival across Bihar/Jharkhand/UP; train bookings saturated, airfares escalate to statutory caps."
    },
    {
        "id": "XMAS2026",
        "name": "Christmas & Year-End Holidays 2026",
        "date": "2026-12-25",
        "window_start": "2026-12-23",
        "window_end": "2027-01-03",
        "category": "Leisure Peak",
        "national_surge_multiplier": 2.5,
        "affected_corridors": ["BOM-GOI", "DEL-GOI", "BLR-COK", "DEL-IXB", "BOM-IXZ"],
        "cultural_context": "Pan-India year-end travel to Goa, Kerala, Northeast, and Andaman."
    },

    # --- 2027 CALENDAR HIGHLIGHTS ---
    {
        "id": "MAK2027",
        "name": "Makar Sankranti / Pongal 2027",
        "date": "2027-01-14",
        "window_start": "2027-01-12",
        "window_end": "2027-01-17",
        "category": "Harvest Festival",
        "national_surge_multiplier": 1.7,
        "affected_corridors": ["DEL-MAA", "BOM-MAA", "BLR-MAA"],
        "cultural_context": "Southern harvest celebration diaspora return."
    },
    {
        "id": "REP2027",
        "name": "Republic Day 2027",
        "date": "2027-01-26",
        "window_start": "2027-01-23",
        "window_end": "2027-01-27",
        "category": "Gazetted Long Weekend",
        "national_surge_multiplier": 1.6,
        "affected_corridors": ["DEL-BOM", "BOM-GOI", "DEL-DED"],
        "cultural_context": "National holiday 4-day travel weekend."
    },
    {
        "id": "HOL2027",
        "name": "Holi Festival 2027",
        "date": "2027-03-22",
        "window_start": "2027-03-19",
        "window_end": "2027-03-24",
        "category": "Major Cultural Festival",
        "national_surge_multiplier": 2.2,
        "affected_corridors": ["BOM-DEL", "BLR-DEL", "BOM-PAT"],
        "cultural_context": "Spring homecoming rush across Northern corridors."
    },
    {
        "id": "EID2027",
        "name": "Eid-ul-Fitr 2027",
        "date": "2027-03-10",
        "window_start": "2027-03-08",
        "window_end": "2027-03-13",
        "category": "Gazetted Festival",
        "national_surge_multiplier": 1.9,
        "affected_corridors": ["DEL-HYD", "BOM-CCU", "DEL-SXR"],
        "cultural_context": "Culmination of Ramadan urban travel."
    },
    {
        "id": "DIW2027",
        "name": "Diwali / Deepavali 2027",
        "date": "2027-10-29",
        "window_start": "2027-10-25",
        "window_end": "2027-11-02",
        "category": "Super-Peak National Festival",
        "national_surge_multiplier": 3.2,
        "affected_corridors": ["BOM-DEL", "DEL-BOM", "DEL-PAT", "BOM-PAT", "DEL-CCU"],
        "cultural_context": "Nationwide festive surge 2027."
    },
    {
        "id": "CHT2027",
        "name": "Chhath Puja 2027",
        "date": "2027-11-04",
        "window_start": "2027-11-02",
        "window_end": "2027-11-07",
        "category": "Major Cultural Festival",
        "national_surge_multiplier": 2.9,
        "affected_corridors": ["DEL-PAT", "BOM-PAT", "BLR-PAT"],
        "cultural_context": "Eastern India solar devotion surge 2027."
    }
]

class IndianFestivalCalendarEngine:
    """
    Engine to identify, quantify, and isolate Indian festival seasonal demand shocks.
    Used by:
      - Hedonic Regression Model (beta_holiday dummy parameter)
      - Autonomous Learning Agent (proactive stratum query allocation)
      - MoSPI Evaluator Defense Dossier (proving composition isolation)
    """

    def __init__(self):
        self.catalog = INDIAN_HOLIDAYS_CATALOG

    def is_holiday_surge(self, date_str: str) -> bool:
        """Determines if a given YYYY-MM-DD date falls in a major festival surge window."""
        try:
            target = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return False

        for h in self.catalog:
            start = datetime.strptime(h["window_start"], "%Y-%m-%d").date()
            end = datetime.strptime(h["window_end"], "%Y-%m-%d").date()
            if start <= target <= end:
                return True
        return False

    def get_festival_for_date(self, date_str: str) -> Optional[Dict[str, Any]]:
        """Returns details of active festival on date, or None."""
        try:
            target = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return None

        for h in self.catalog:
            start = datetime.strptime(h["window_start"], "%Y-%m-%d").date()
            end = datetime.strptime(h["window_end"], "%Y-%m-%d").date()
            if start <= target <= end:
                return h
        return None

    def get_corridor_festival_impact(self, route: str, date_str: str) -> Dict[str, Any]:
        """
        Calculates corridor-specific elasticity impact for a route on a specific date.
        Returns expected demand shock multiplier and hedonic coefficient adjustment.
        """
        fest = self.get_festival_for_date(date_str)
        if not fest:
            return {
                "is_festival_window": False,
                "festival_name": None,
                "demand_multiplier": 1.0,
                "hedonic_beta_holiday": 0.0,
                "corridor_targeted": False
            }

        route_upper = route.upper()
        is_targeted = any(route_upper == c or route_upper.split("-")[::-1] == c.split("-") for c in fest["affected_corridors"])
        
        multiplier = fest["national_surge_multiplier"] if is_targeted else (1.0 + (fest["national_surge_multiplier"] - 1.0) * 0.4)
        beta_holiday = 0.284 if is_targeted else 0.115

        return {
            "is_festival_window": True,
            "festival_name": fest["name"],
            "category": fest["category"],
            "demand_multiplier": multiplier,
            "hedonic_beta_holiday": beta_holiday,
            "corridor_targeted": is_targeted,
            "cultural_context": fest["cultural_context"]
        }

    def get_upcoming_festivals(self, from_date_str: Optional[str] = None, horizon_days: int = 60) -> List[Dict[str, Any]]:
        """Finds all festivals in the next N days from today."""
        if not from_date_str:
            base_date = datetime.now().date()
        else:
            try:
                base_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
            except Exception:
                base_date = datetime.now().date()

        end_date = base_date + timedelta(days=horizon_days)
        upcoming = []

        for h in self.catalog:
            h_date = datetime.strptime(h["date"], "%Y-%m-%d").date()
            if base_date <= h_date <= end_date:
                days_away = (h_date - base_date).days
                item = dict(h)
                item["days_until_festival"] = days_away
                upcoming.append(item)

        upcoming.sort(key=lambda x: x["days_until_festival"])
        return upcoming

    def get_full_calendar_view(self) -> List[Dict[str, Any]]:
        """Returns the complete 2026-2027 Indian Cultural Calendar with surge metrics."""
        return self.catalog

indian_calendar = IndianFestivalCalendarEngine()
