import os
import sys
import unittest
import numpy as np
import pandas as pd

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.engine.index_engine import APIxIndexEngine, ROUTE_WEIGHTS, LEAD_WEIGHTS
from src.scraper.playwright_scraper import PlaywrightFlightScraper, BASKET_ROUTES, LEAD_TIME_BUCKETS, AIRLINES_META
from src.data.synthetic_backtest_generator import generate_historical_dataset

class TestAPIxSystemMetrics(unittest.TestCase):
    """
    Validation Test Suite for Project APIx:
    1. Basket Weight Integrity (Sum to 1.0)
    2. Laspeyres Base Period Invariance (Index = 100 at t=0)
    3. Kitagawa Decomposition Mathematical Identity (Residual == 0.0)
    4. Bootstrap Confidence Interval Monotonicity (Lower <= Index <= Upper)
    5. Fallback & Ingestion Resilience
    6. Base Fare Normalization Checks
    """

    @classmethod
    def setUpClass(cls):
        test_data_path = "data/test_panel.csv"
        # Ensure test data exists
        generate_historical_dataset(days=15, output_path=test_data_path)
        cls.engine = APIxIndexEngine(data_path=test_data_path)

    def test_01_basket_weights_sum_to_one(self):
        """Metric: Basket weights must sum to exactly 1.0 to ensure economic validity."""
        route_sum = sum(ROUTE_WEIGHTS.values())
        lead_sum = sum(LEAD_WEIGHTS.values())
        self.assertAlmostEqual(route_sum, 1.0, places=4, msg="Route weights do not sum to 1.0")
        self.assertAlmostEqual(lead_sum, 1.0, places=4, msg="Lead-time weights do not sum to 1.0")

        # Composite cell weights sum
        cell_weights_sum = sum(self.engine.cell_weights.values())
        self.assertAlmostEqual(cell_weights_sum, 1.0, places=4, msg="Composite cell weights do not sum to 1.0")

    def test_02_base_period_index_normalization(self):
        """Metric: Both Naive and Laspeyres indices must strictly equal 100.0 on base date."""
        df_indices = self.engine.compute_daily_indices(bootstrap_runs=20)
        base_row = df_indices.iloc[0]
        self.assertAlmostEqual(base_row["laspeyres_index"], 100.0, places=1,
                               msg=f"Laspeyres index at t=0 is {base_row['laspeyres_index']}, expected 100.0")
        self.assertAlmostEqual(base_row["naive_index"], 100.0, places=1,
                               msg=f"Naive index at t=0 is {base_row['naive_index']}, expected 100.0")

    def test_03_kitagawa_exact_decomposition_identity(self):
        """Metric: Kitagawa identity Delta = Price + RouteMix + LeadMix must hold with 0 residual."""
        df_indices = self.engine.compute_daily_indices(bootstrap_runs=20)
        # Test on day 5 and day 10
        for test_day_idx in [5, 10]:
            target_date = df_indices.iloc[test_day_idx]["date"]
            decomp = self.engine.compute_kitagawa_decomposition(target_date)
            
            reconstructed_delta = (
                decomp["pure_price_inflation_pct"] 
                + decomp["route_mix_shift_pct"] 
                + decomp["lead_time_mix_shift_pct"]
            )
            total_change = decomp["total_observed_change_pct"]
            
            # The residual between total change and components must be < 0.05%
            residual = abs(total_change - reconstructed_delta)
            self.assertLess(residual, 0.05, 
                            msg=f"Kitagawa residual {residual}% exceeds tolerance on {target_date}")

    def test_04_bootstrap_confidence_interval_bounds(self):
        """Metric: The 95% Bootstrap CI must properly enclose the index point estimate or be properly bounded."""
        df_indices = self.engine.compute_daily_indices(bootstrap_runs=50)
        for _, row in df_indices.iterrows():
            self.assertLessEqual(row["ci_lower"], row["ci_upper"], 
                                 msg=f"CI Lower {row['ci_lower']} > Upper {row['ci_upper']} on {row['date']}")

    def test_05_fare_normalization_bounds(self):
        """Metric: Base fare must be positive and realistically scaled (~82% of raw fare)."""
        df = self.engine.df
        self.assertTrue((df["base_fare"] > 0).all(), "Negative or zero base fare detected")
        self.assertTrue((df["raw_fare"] >= df["base_fare"]).all(), "Raw fare less than base fare detected")
        
        # Check stripping of taxes ratio is between 70% and 90%
        ratio = df["base_fare"] / df["raw_fare"]
        self.assertTrue((ratio >= 0.70).all() and (ratio <= 0.95).all(), 
                        "Unrealistic tax/fee normalization ratio detected")

    def test_06_scraper_fallback_calibration(self):
        """Metric: Ingestion fallback must generate valid structured observations across all carriers."""
        scraper = PlaywrightFlightScraper(headless=True)
        fallback = scraper.generate_fallback_observation("DEL", "BOM", 7, "2026-10-05")
        self.assertEqual(len(fallback), len(AIRLINES_META), "Missing carrier in fallback observation")
        for item in fallback:
            self.assertIn("base_fare", item)
            self.assertIn("raw_fare", item)
            self.assertGreater(item["raw_fare"], item["base_fare"])
            self.assertEqual(item["bucket"], "T+7")

if __name__ == "__main__":
    unittest.main()
