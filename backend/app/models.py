from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from datetime import datetime
from backend.app.database import Base

class FlightObservation(Base):
    __tablename__ = "flight_observations"

    id = Column(Integer, primary_key=True, index=True)
    date_collected = Column(String, index=True)
    flight_date = Column(String, index=True)
    route = Column(String, index=True)
    origin = Column(String, index=True)
    destination = Column(String, index=True)
    lead_bucket = Column(String, index=True)
    lead_days = Column(Integer)
    airline = Column(String, index=True)
    raw_fare = Column(Float)
    base_fare = Column(Float)
    source = Column(String, default="Playwright-Ingestor")
    sampling_shock = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyIndex(Base):
    __tablename__ = "daily_indices"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, unique=True, index=True)
    naive_avg_fare = Column(Float)
    naive_index = Column(Float)
    laspeyres_index = Column(Float)
    ci_lower = Column(Float)
    ci_upper = Column(Float)
    divergence_pct_points = Column(Float)
    pure_price_pct = Column(Float, nullable=True)
    route_mix_pct = Column(Float, nullable=True)
    lead_time_mix_pct = Column(Float, nullable=True)
    total_observations = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class DGCAReference(Base):
    __tablename__ = "dgca_reference"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(String, unique=True, index=True)
    dgca_avg_fare = Column(Float)
    passenger_volume_million = Column(Float)
    cpi_transport_subindex = Column(Float)
