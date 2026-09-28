import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_historical_dataset(days: int = 40, output_path: str = "data/historical_airfare_panel.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    random.seed(42)
    np.random.seed(42)

    routes = [
        {"route": "DEL-BOM", "base_price": 5200, "weight": 0.22},
        {"route": "BOM-DEL", "base_price": 5200, "weight": 0.20},
        {"route": "DEL-BLR", "base_price": 6400, "weight": 0.16},
        {"route": "BOM-BLR", "base_price": 4100, "weight": 0.12},
        {"route": "DEL-CCU", "base_price": 5800, "weight": 0.10},
        {"route": "BLR-HYD", "base_price": 3200, "weight": 0.08},
        {"route": "MAA-DEL", "base_price": 6100, "weight": 0.06},
        {"route": "DEL-PNQ", "base_price": 4800, "weight": 0.06},
    ]

    lead_times = [
        {"bucket": "T+1", "days": 1, "multiplier": 1.95, "weight": 0.15},
        {"bucket": "T+7", "days": 7, "multiplier": 1.38, "weight": 0.25},
        {"bucket": "T+15", "days": 15, "multiplier": 1.05, "weight": 0.30},
        {"bucket": "T+30", "days": 30, "multiplier": 0.90, "weight": 0.20},
        {"bucket": "T+45", "days": 45, "multiplier": 0.80, "weight": 0.10},
    ]

    airlines = [
        {"name": "IndiGo", "market_share": 0.650, "price_factor": 0.95},
        {"name": "Air India", "market_share": 0.267, "price_factor": 1.12},
        {"name": "Akasa Air", "market_share": 0.055, "price_factor": 0.92},
        {"name": "SpiceJet", "market_share": 0.012, "price_factor": 0.90},
    ]

    start_date = datetime(2026, 8, 1)
    records = []

    # Simulation parameters:
    # 1. Steady mild aviation turbine fuel (ATF) inflation: +3.8% over the 40 days
    # 2. Week 3 (Days 15-22): An OTA website sampling distortion where naive scraping 
    #    samples 3x more T+1 emergency flights due to festive page banner shifts.
    for day_idx in range(days):
        current_date = start_date + timedelta(days=day_idx)
        date_str = current_date.strftime("%Y-%m-%d")

        # True macroeconomic price drift
        macro_inflation_factor = 1.0 + (0.042 * (day_idx / days)) + (np.sin(day_idx / 5.0) * 0.008)

        # Mix shock flag (simulating naive scraper bias)
        is_sampling_shock_period = (15 <= day_idx <= 23)

        for r in routes:
            for lt in lead_times:
                # Determine how many flights are sampled
                sample_count = 5
                if is_sampling_shock_period:
                    if lt["bucket"] == "T+1":
                        sample_count = 14  # naive scraper disproportionately pulls last-minute fares!
                    elif lt["bucket"] in ["T+30", "T+45"]:
                        sample_count = 2   # under-sampling advance bookings
                
                for _ in range(sample_count):
                    # Choose airline probabilistically based on DGCA market share
                    airline_obj = random.choices(airlines, weights=[a["market_share"] for a in airlines])[0]
                    
                    true_cell_base = (
                        r["base_price"] 
                        * lt["multiplier"] 
                        * airline_obj["price_factor"] 
                        * macro_inflation_factor
                    )
                    # Small idiosyncratic noise per flight
                    noise = np.random.normal(1.0, 0.035)
                    final_base_fare = round(true_cell_base * noise, 2)
                    raw_fare = int(final_base_fare * 1.22)  # Base fare + 22% taxes/UDF/fees

                    records.append({
                        "date_collected": date_str,
                        "day_index": day_idx,
                        "route": r["route"],
                        "origin": r["route"].split("-")[0],
                        "destination": r["route"].split("-")[1],
                        "lead_bucket": lt["bucket"],
                        "lead_days": lt["days"],
                        "airline": airline_obj["name"],
                        "base_fare": final_base_fare,
                        "raw_fare": raw_fare,
                        "flight_date": (current_date + timedelta(days=lt["days"])).strftime("%Y-%m-%d"),
                        "sampling_shock": is_sampling_shock_period and (lt["bucket"] == "T+1")
                    })

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} flight records across {days} days saved to {output_path}")

    # Generate DGCA monthly reference benchmark
    dgca_ref = pd.DataFrame([
        {"month": "July 2026", "dgca_avg_fare": 5420, "passenger_volume_million": 12.95, "cpi_transport_subindex": 178.4},
        {"month": "August 2026", "dgca_avg_fare": 5510, "passenger_volume_million": 12.13, "cpi_transport_subindex": 179.8},
        {"month": "September 2026 (Est.)", "dgca_avg_fare": 5590, "passenger_volume_million": 12.40, "cpi_transport_subindex": 181.2},
    ])
    dgca_path = "data/dgca_monthly_reference.csv"
    dgca_ref.to_csv(dgca_path, index=False)
    print(f"Generated DGCA reference benchmarks saved to {dgca_path}")
    return df

if __name__ == "__main__":
    generate_historical_dataset()
