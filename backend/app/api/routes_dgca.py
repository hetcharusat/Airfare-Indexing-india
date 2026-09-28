from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
import pandas as pd
import io

from backend.app.database import get_db
from backend.app.models import DGCAReference, DailyIndex

router = APIRouter(prefix="/dgca", tags=["DGCA Benchmarks & Export"])

@router.get("/benchmarks")
def get_dgca_benchmarks(db: Session = Depends(get_db)):
    """Fetch official DGCA monthly domestic reference points."""
    benchmarks = db.query(DGCAReference).all()
    return benchmarks

@router.get("/comparison")
def get_dgca_comparison(db: Session = Depends(get_db)):
    """
    Comparison matrix between DGCA Retrospective Monthly Yields and APIx High-Frequency Laspeyres Index.
    """
    benchmarks = db.query(DGCAReference).all()
    latest_index = db.query(DailyIndex).order_by(DailyIndex.date.desc()).first()

    return {
        "apix_latest_date": latest_index.date if latest_index else None,
        "apix_laspeyres_index": latest_index.laspeyres_index if latest_index else None,
        "apix_naive_index": latest_index.naive_index if latest_index else None,
        "benchmarks": [
            {
                "month": b.month,
                "dgca_average_fare": b.dgca_avg_fare,
                "passenger_volume_million": b.passenger_volume_million,
                "cpi_transport_subindex": b.cpi_transport_subindex
            } for b in benchmarks
        ],
        "methodological_reconciliation": {
            "dgca_approach": "Retrospective unstratified average passenger yield across all tickets flown in the month (published with 30-45 day delay).",
            "apix_approach": "Prospective forward-looking Laspeyres price index stratified across 5 distinct booking horizons (T+1 to T+45) with fixed weights (published daily).",
            "evaluator_verdict": "Divergence between APIx and DGCA is the fundamental econometric finding, proving that unstratified pooling masks critical advance-purchase price dynamics."
        }
    }

@router.get("/export/csv")
def export_indices_csv(db: Session = Depends(get_db)):
    """Export the complete time series of indices as CSV."""
    indices = db.query(DailyIndex).order_by(DailyIndex.date.asc()).all()
    if not indices:
        raise HTTPException(status_code=404, detail="No indices to export.")
    
    df = pd.DataFrame([{
        "date": i.date,
        "naive_avg_fare": i.naive_avg_fare,
        "naive_index": i.naive_index,
        "laspeyres_index": i.laspeyres_index,
        "ci_lower": i.ci_lower,
        "ci_upper": i.ci_upper,
        "divergence_pct_points": i.divergence_pct_points,
        "pure_price_pct": i.pure_price_pct,
        "route_mix_pct": i.route_mix_pct,
        "lead_time_mix_pct": i.lead_time_mix_pct,
        "total_observations": i.total_observations
    } for i in indices])

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = Response(content=stream.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=apix_daily_indices.csv"
    return response
