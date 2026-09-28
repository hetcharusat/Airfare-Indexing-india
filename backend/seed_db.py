import os
import sys
import pandas as pd
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import FlightObservation, DailyIndex, DGCAReference
from backend.app.services.index_calculator import calculator_service

def seed_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Seed Flight Observations
    panel_file = "data/historical_airfare_panel.csv"
    if os.path.exists(panel_file):
        count_existing = db.query(FlightObservation).count()
        if count_existing == 0:
            print(f"Loading flight observations from {panel_file}...")
            df = pd.read_csv(panel_file)
            batch = []
            for _, row in df.iterrows():
                obs = FlightObservation(
                    date_collected=row["date_collected"],
                    flight_date=row["flight_date"],
                    route=row["route"],
                    origin=row["origin"],
                    destination=row["destination"],
                    lead_bucket=row["lead_bucket"],
                    lead_days=int(row["lead_days"]),
                    airline=row["airline"],
                    raw_fare=float(row["raw_fare"]),
                    base_fare=float(row["base_fare"]),
                    source="Synthetic-Historical-Ingestor",
                    sampling_shock=bool(row["sampling_shock"])
                )
                batch.append(obs)
                if len(batch) >= 1000:
                    db.bulk_save_objects(batch)
                    db.commit()
                    batch = []
            if batch:
                db.bulk_save_objects(batch)
                db.commit()
            print(f"Successfully inserted {len(df)} flight observations.")
        else:
            print(f"Flight observations already populated ({count_existing} rows).")

    # 2. Seed DGCA Monthly Reference
    dgca_file = "data/dgca_monthly_reference.csv"
    if os.path.exists(dgca_file):
        count_dgca = db.query(DGCAReference).count()
        if count_dgca == 0:
            print(f"Loading DGCA reference from {dgca_file}...")
            df_dgca = pd.read_csv(dgca_file)
            for _, r in df_dgca.iterrows():
                db_ref = DGCAReference(
                    month=r["month"],
                    dgca_avg_fare=float(r["dgca_avg_fare"]),
                    passenger_volume_million=float(r["passenger_volume_million"]),
                    cpi_transport_subindex=float(r["cpi_transport_subindex"])
                )
                db.add(db_ref)
            db.commit()
            print("Successfully populated DGCA monthly reference data.")

    # 3. Compute and store daily indices
    print("Computing and caching initial Daily Indices...")
    calculator_service.recompute_all_indices(db, bootstrap_runs=100)
    print("Database seeding completed successfully!")
    db.close()

if __name__ == "__main__":
    seed_database()
