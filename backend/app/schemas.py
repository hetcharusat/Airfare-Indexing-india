from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class FlightObservationSchema(BaseModel):
    id: Optional[int] = None
    date_collected: str
    flight_date: str
    route: str
    origin: str
    destination: str
    lead_bucket: str
    lead_days: int
    airline: str
    raw_fare: float
    base_fare: float
    source: str
    sampling_shock: bool

    class Config:
        from_attributes = True


class DailyIndexSchema(BaseModel):
    id: Optional[int] = None
    date: str
    naive_avg_fare: float
    naive_index: float
    laspeyres_index: float
    ci_lower: float
    ci_upper: float
    divergence_pct_points: float
    pure_price_pct: Optional[float] = None
    route_mix_pct: Optional[float] = None
    lead_time_mix_pct: Optional[float] = None
    total_observations: int

    class Config:
        from_attributes = True


class KitagawaDecompositionSchema(BaseModel):
    target_date: str
    base_date: str
    base_fare: float
    target_fare: float
    total_observed_change_pct: float
    pure_price_inflation_pct: float
    route_mix_shift_pct: float
    lead_time_mix_shift_pct: float
    residual_unexplained: float


class ScrapeTriggerRequest(BaseModel):
    origin: str
    destination: str
    lead_days: int


class ScrapeTriggerResponse(BaseModel):
    status: str
    message: str
    records_count: int
    sample_records: List[Dict[str, Any]]


class PolicyShockRequest(BaseModel):
    shock_type: str  # e.g. "atf_surge", "festive_demand"
    magnitude_pct: float  # e.g. 15.0
    start_date: str
    duration_days: int


class SystemSummarySchema(BaseModel):
    total_observations: int
    total_days: int
    latest_date: str
    latest_laspeyres_index: float
    latest_naive_index: float
    peak_overstatement_pts: float
    peak_overstatement_date: str
    basket_routes_count: int
    airlines_tracked: List[str]
