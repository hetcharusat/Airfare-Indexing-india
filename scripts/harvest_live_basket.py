import os
import sys
import time
import logging
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.database import SessionLocal, Base, engine
from backend.app.models import FlightObservation
from backend.app.services.index_calculator import calculator_service
from src.scraper.scraper_manager import scraper_manager
from src.scraper.playwright_scraper import BASKET_ROUTES, LEAD_TIME_BUCKETS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LiveBasketHarvester")

def harvest_entire_live_basket(corridors_limit: int = None, max_flights_per_cell: int = 6):
    """
    Orchestrates 100% genuine live scraping across the fixed DGCA basket corridors and lead times.
    Uses 3-Tier Multi-Engine Ingestion (Duffel GDS, Air India Calendar, Playwright).
    """
    logger.info("Initializing 3-Tier Hybrid Basket Harvester (Zero Mock Data Policy)...")
    db = SessionLocal()

    routes_to_scrape = BASKET_ROUTES[:corridors_limit] if corridors_limit else BASKET_ROUTES
    total_cells = len(routes_to_scrape) * len(LEAD_TIME_BUCKETS)
    cell_idx = 0
    total_saved = 0

    logger.info(f"Starting sweep across {len(routes_to_scrape)} corridors and {len(LEAD_TIME_BUCKETS)} lead windows ({total_cells} cells)...")

    for r in routes_to_scrape:
        origin = r["origin"]
        dest = r["destination"]
        for b in LEAD_TIME_BUCKETS:
            cell_idx += 1
            lead_days = b["days"]
            bucket = b["bucket"]
            
            logger.info(f"[{cell_idx}/{total_cells}] Scraping LIVE: {origin}->{dest} ({bucket}, {lead_days} days out)...")
            try:
                flights = scraper_manager.harvest_stratum(origin, dest, lead_days, max_flights=max_flights_per_cell)
                for f in flights:
                    obs = FlightObservation(
                        date_collected=f["date_collected"],
                        flight_date=f["flight_date"],
                        route=f["route"],
                        origin=f["origin"],
                        destination=f["destination"],
                        lead_bucket=f["lead_bucket"],
                        lead_days=f["lead_days"],
                        airline=f["airline"],
                        raw_fare=f["raw_fare"],
                        base_fare=f["base_fare"],
                        source=f["source"],
                        sampling_shock=False
                    )
                    db.add(obs)
                    total_saved += 1
                db.commit()
                logger.info(f"  --> Saved {len(flights)} real flight observations for {origin}->{dest} ({bucket}).")
            except Exception as e:
                logger.warning(f"  --> Skipped {origin}->{dest} ({bucket}): {e}")

            time.sleep(1.0)  # Respectful network delay

    logger.info(f"Harvest complete! Successfully persisted {total_saved} 100% REAL flights into database.")
    
    # Recalculate official indices
    logger.info("Recomputing official APIx Laspeyres indices across real observations...")
    calculator_service.recompute_all_indices(db, bootstrap_runs=100)
    logger.info("Indices successfully recomputed and cached in database.")
    db.close()

if __name__ == "__main__":
    # Harvest top 3 corridors for quick validation run
    harvest_entire_live_basket(corridors_limit=3, max_flights_per_cell=5)
