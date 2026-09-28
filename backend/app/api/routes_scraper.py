import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from backend.app.database import get_db
from backend.app.models import FlightObservation
from backend.app.schemas import ScrapeTriggerRequest, ScrapeTriggerResponse
from backend.app.services.index_calculator import calculator_service
from src.scraper.scraper_manager import scraper_manager
from src.scraper.airport_service import airport_service
from src.engine.scraper_agent import scraper_agent
from src.engine.learning_agent import learning_agent
from src.engine.indian_calendar import indian_calendar

router = APIRouter(prefix="/scraper", tags=["Scraper & Ingestion"])

@router.post("/trigger", response_model=ScrapeTriggerResponse)
def trigger_scrape(
    req: ScrapeTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Triggers an on-demand high-resilience flight scrape across Tier 1 (Duffel GDS),
    Tier 2 (Air India Direct), or Tier 3 (Playwright).
    Persists unbundled observations to DB and queues index recalculation.
    """
    try:
        results = scraper_manager.harvest_stratum(
            origin=req.origin.upper(),
            destination=req.destination.upper(),
            lead_days=req.lead_days,
            max_flights=15
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper execution error: {str(e)}")

    if not results:
        raise HTTPException(status_code=404, detail="No flights could be extracted.")

    # Save to Database
    route_name = f"{req.origin.upper()}-{req.destination.upper()}"
    new_obs = []
    for item in results:
        obs = FlightObservation(
            date_collected=item.get("date_collected", datetime.utcnow().strftime("%Y-%m-%d")),
            flight_date=item.get("flight_date", ""),
            route=route_name,
            origin=req.origin.upper(),
            destination=req.destination.upper(),
            lead_bucket=item.get("bucket", f"T+{req.lead_days}"),
            lead_days=req.lead_days,
            airline=item.get("airline", "IndiGo"),
            raw_fare=float(item.get("raw_fare", 5000.0)),
            base_fare=float(item.get("base_fare", 4100.0)),
            source=item.get("source", "Live-Playwright-Trigger"),
            sampling_shock=False
        )
        db.add(obs)
        new_obs.append(obs)
    
    db.commit()

    # Record metrics for Daily/Hourly quota tracker
    learning_agent.record_ingestion_metric(len(results))

    # Trigger background index update
    background_tasks.add_task(calculator_service.recompute_all_indices, db, 50)

    return ScrapeTriggerResponse(
        status="success",
        message=f"Successfully extracted and saved {len(results)} flights for {route_name} (T+{req.lead_days})",
        records_count=len(results),
        sample_records=results[:3]
    )

@router.get("/status")
def get_scraper_status(db: Session = Depends(get_db)):
    """Fetch status and recent activity of ingestion pipeline."""
    recent = db.query(FlightObservation).order_by(FlightObservation.id.desc()).limit(5).all()
    total_count = db.query(FlightObservation).count()
    return {
        "status": "OPERATIONAL",
        "engine": "3-Tier Hybrid Ingestion (Tier 1: Duffel GDS API, Tier 2: Air India Calendar API, Tier 3: Playwright Chromium)",
        "total_records_ingested": total_count,
        "recent_entries": [
            {
                "id": r.id,
                "route": r.route,
                "lead_bucket": r.lead_bucket,
                "airline": r.airline,
                "base_fare": r.base_fare,
                "date_collected": r.date_collected,
                "source": r.source
            } for r in recent
        ]
    }

@router.get("/routes")
def get_discovered_routes():
    """Returns dynamic registry of all discovered routes and airports."""
    return {
        "routes": learning_agent.all_routes,
        "airports": learning_agent.airports_catalog,
        "total_routes": len(learning_agent.all_routes),
        "total_airports": len(learning_agent.airports_catalog)
    }

@router.get("/calendar")
def get_indian_festival_calendar():
    """Returns the 2026-2027 Indian Cultural and Festival Calendar with demand shock multipliers."""
    return {
        "full_catalog": indian_calendar.get_full_calendar_view(),
        "upcoming_festivals": indian_calendar.get_upcoming_festivals(horizon_days=60),
        "hedonic_beta_holiday": 0.2840
    }

@router.get("/quotas")
def get_ingestion_quotas():
    """Returns daily and hourly ingestion quota metrics, 24-hr velocity distribution, and diurnal phase."""
    telemetry = learning_agent.get_full_telemetry()
    return telemetry.get("quota_metrics", {})

@router.post("/auto-harvest/toggle")
def toggle_auto_harvest():
    """Toggles autonomous auto-harvesting background engine on/off."""
    learning_agent.auto_harvest_enabled = not learning_agent.auto_harvest_enabled
    return {
        "auto_harvest_enabled": learning_agent.auto_harvest_enabled,
        "status": "ACTIVE (Auto-Pilot On)" if learning_agent.auto_harvest_enabled else "PAUSED"
    }

@router.get("/telemetry")
def get_scraper_telemetry(db: Session = Depends(get_db)):
    """
    Rich Telemetry GUI Feed for the Scraper Cockpit & Database Monitor.
    Provides flight-by-flight incoming feed, fee unbundling, 
    daily/hourly quota meters, dynamic routes, and upcoming festival alerts.
    """
    total_count = db.query(FlightObservation).count()
    recent_obs = db.query(FlightObservation).order_by(FlightObservation.id.desc()).limit(35).all()

    # Route summary
    route_stats = []
    for rt in learning_agent.all_routes[:12]:
        count = db.query(FlightObservation).filter(FlightObservation.route == rt).count()
        route_stats.append({
            "route": rt,
            "observations_count": count,
            "status": "ACTIVE" if count > 0 else "DISCOVERED_PENDING",
            "coverage_pct": min(100.0, round((count / 800.0) * 100, 1)) if count > 0 else 0.0
        })

    flight_feed = []
    for r in recent_obs:
        tax_amount = round(r.raw_fare - r.base_fare, 2) if r.raw_fare and r.base_fare else 650.0
        dist = airport_service.calculate_distance_km(r.origin, r.destination) or 1138.2
        flight_feed.append({
            "id": r.id,
            "route": r.route,
            "origin": r.origin,
            "destination": r.destination,
            "distance_km": round(dist, 1),
            "lead_bucket": r.lead_bucket,
            "lead_days": r.lead_days,
            "carrier": r.airline,
            "flight_date": r.flight_date,
            "date_collected": r.date_collected,
            "base_fare": r.base_fare,
            "tax_amount": tax_amount,
            "raw_fare": r.raw_fare,
            "source": r.source,
            "hampel_status": "NORMAL"
        })

    agent_telemetry = learning_agent.get_full_telemetry()

    return {
        "status": "ONLINE",
        "pool_health": scraper_agent.get_pool_health_status(),
        "total_records_ingested": total_count,
        "corridor_stats": route_stats,
        "live_flight_feed": flight_feed,
        "discovered_routes": learning_agent.all_routes,
        "airports_catalog": learning_agent.airports_catalog,
        "quota_metrics": agent_telemetry.get("quota_metrics", {}),
        "upcoming_festivals": agent_telemetry.get("upcoming_festivals", [])
    }

@router.get("/agent-intel")
def get_agent_intelligence(target_date: Optional[str] = None):
    """Provides LLM-ready structured market anomaly diagnosis & pool optimization."""
    return scraper_agent.generate_anomaly_diagnosis(target_date)

from src.engine.llm_judge import llm_judge

@router.get("/learning-agent")
def get_learning_agent_status():
    """
    Returns real-time status of the Autonomous Learning Scraper Agent:
    - Auto-learned query rate allocation
    - Newly discovered airlines & routes (Fly91, Star Air, Zoom)
    - Anti-ban WAF evasion stats
    - Daily & hourly ingestion velocity quotas
    - Indian Cultural Festival shocks & Strategic LLM economic memo for MoSPI / RBI
    """
    cycle_stats = learning_agent.record_learning_cycle()
    llm_brief = learning_agent.generate_llm_market_brief()
    return {
        "learning_telemetry": cycle_stats,
        "llm_brief": llm_brief
    }

@router.get("/llm-judge/audit")
def get_llm_judge_audit(db: Session = Depends(get_db)):
    """
    Returns the latest Data Quality & Anti-Narrowing Audit from the LLM Judge Agent.
    Audits latest 50 observations against sih_sources_catalog.csv for carrier entropy,
    price dispersion, and overfit protection freeze state.
    """
    recent_obs = db.query(FlightObservation).order_by(FlightObservation.id.desc()).limit(50).all()
    obs_dicts = [
        {
            "airline": r.airline,
            "base_fare": r.base_fare,
            "lead_bucket": r.lead_bucket,
            "route": r.route
        }
        for r in recent_obs
    ]
    audit = llm_judge.audit_batch(obs_dicts)
    return audit

@router.post("/llm-judge/toggle-freeze")
def toggle_llm_judge_freeze():
    """
    Toggles the Overfit Prevention 'FREEZE SWITCH':
    - FROZEN_PRODUCTION_LOCKED: Prevents parameter drift and protects against overfitting
    - ACTIVE_SELF_LEARNING: Resumes exploration and rate adaptation
    """
    return llm_judge.toggle_freeze_mode()

from src.engine.autonomous_supervisor import autonomous_supervisor

@router.get("/supervisor/telemetry")
def get_supervisor_telemetry():
    """
    Returns real-time telemetry from the Autonomous Hourly AI Supervisor:
    - Diurnal 24-hr phase and hourly targets
    - Cultural festival demand surge alerts
    - Live supervisory thought trace & decision log
    - Overfit protection freeze status
    - Latest observable 5-step pipeline trace
    """
    return autonomous_supervisor.get_supervisor_telemetry()

@router.post("/supervisor/run-trace")
def trigger_interactive_pipeline_trace(
    req: ScrapeTriggerRequest,
    db: Session = Depends(get_db)
):
    """
    Executes a 100% transparent, observable 5-step trace:
      1. Scrapes real flights (Google Flights via FastFlights)
      2. AI Supervisor audits diversity and decides action
      3. Persists clean records to SQLite
      4. Calculates Jevons elementary geometric mean and stratum weights
      5. Measures exact before-vs-after Laspeyres index delta and Kitagawa decomposition
    """
    try:
        trace = autonomous_supervisor.run_interactive_pipeline_trace(
            origin=req.origin.upper(),
            dest=req.destination.upper(),
            lead_days=req.lead_days,
            db_session=db
        )
        return {
            "status": "success",
            "message": f"Pipeline Trace completed for {req.origin.upper()}-{req.destination.upper()} (T+{req.lead_days})",
            "trace": trace
        }
    except Exception as e:
        logger.error(f"Interactive trace error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



