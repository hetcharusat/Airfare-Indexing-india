import threading
import time
import logging
from datetime import datetime
from backend.app.database import SessionLocal
from backend.app.models import FlightObservation
from backend.app.services.index_calculator import calculator_service
from src.engine.learning_agent import learning_agent
from src.scraper.scraper_manager import scraper_manager

logger = logging.getLogger("APIxScheduler")

from src.engine.autonomous_supervisor import autonomous_supervisor

class BackgroundIngestionScheduler:
    """
    Autonomous background worker for Project APIx.
    Perpetually runs:
      1. Autonomous AI Supervisor loop (Audit, Self-healing, Hourly Cadence, Reindex)
      2. Autonomous Learning Agent loop (Q-value updates, route & carrier discovery)
      3. Quota & Velocity tracking across Indian domestic routes
    """
    def __init__(self, interval_seconds: int = 15):
        self.interval_seconds = interval_seconds
        self.running = False
        self._thread = None
        self._harvest_tick = 0

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            logger.info("Autonomous Ingestion & Learning Agent Scheduler started.")

    def stop(self):
        self.running = False
        logger.info("Autonomous Ingestion & Learning Agent Scheduler stopped.")

    def _run_loop(self):
        while self.running:
            try:
                # 1. Trigger learning agent cycle (decay epsilon, discover routes, update Q-values)
                cycle_data = learning_agent.record_learning_cycle()
                
                # 2. Autonomous Supervisory Cycle (every 4 cycles = ~60s)
                self._harvest_tick += 1
                if learning_agent.auto_harvest_enabled and self._harvest_tick % 4 == 0:
                    db = SessionLocal()
                    try:
                        autonomous_supervisor.run_hourly_supervisory_cycle(db)
                    finally:
                        db.close()
                elif learning_agent.auto_harvest_enabled and self._harvest_tick % 2 == 0:
                    self._perform_autonomous_harvest()

            except Exception as e:
                logger.error(f"Supervisor background loop error: {e}")
            time.sleep(self.interval_seconds)

    def _perform_autonomous_harvest(self):
        """Autonomously harvests a stratum chosen by MAB and persists to DB."""
        target = learning_agent.get_next_stratum_to_harvest()
        orig = target["origin"]
        dest = target["destination"]
        lead = target["lead_days"]
        route = f"{orig}-{dest}"

        logger.info(f"[Auto-Harvester] Autonomous scrape triggered for {route} (T+{lead})...")

        db = SessionLocal()
        try:
            results = scraper_manager.harvest_stratum(
                origin=orig,
                destination=dest,
                lead_days=lead,
                max_flights=8
            )
            if results:
                for item in results:
                    obs = FlightObservation(
                        date_collected=item.get("date_collected", datetime.utcnow().strftime("%Y-%m-%d")),
                        flight_date=item.get("flight_date", ""),
                        route=route,
                        origin=orig,
                        destination=dest,
                        lead_bucket=item.get("bucket", f"T+{lead}"),
                        lead_days=lead,
                        airline=item.get("airline", "IndiGo"),
                        raw_fare=float(item.get("raw_fare", 5000.0)),
                        base_fare=float(item.get("base_fare", 4100.0)),
                        source=item.get("source", "Autonomous-Agent-Harvest"),
                        sampling_shock=False
                    )
                    db.add(obs)
                db.commit()
                learning_agent.record_ingestion_metric(len(results))
                logger.info(f"[Auto-Harvester] Successfully saved {len(results)} flights for {route} (T+{lead}). Daily total: {learning_agent.daily_ingested_today}")
        except Exception as err:
            logger.warning(f"[Auto-Harvester] Ingestion error: {err}")
            db.rollback()
        finally:
            db.close()

scheduler = BackgroundIngestionScheduler(interval_seconds=15)
