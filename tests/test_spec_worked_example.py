import unittest
import numpy as np
from src.engine.fisher_engine import APIxFisherIndexEngine
from src.engine.outlier_filter import hampel_filter
from src.engine.hedonic_regressor import hedonic_regressor
from src.scraper.airport_service import airport_service

class TestAPIxBuildSpecification(unittest.TestCase):
    """
    Unit Tests for Chapter 7 Worked Numerical Example and Build Checklist
    of SIH26056 Technical Build Specification.
    """

    def test_chapter_7_worked_numerical_example(self):
        """
        Chapter 7 Verification:
          Item           p_i,0  p_i,t  q_i,0  q_i,t  w_i^(0)
          DEL-BOM, T+7   4000   4600   1000   900    0.444
          DEL-BLR, T+30  3500   3600   800    820    0.311
          BOM-BLR, T+1   5000   6200   500    400    0.245
          
        Expected values:
          Laspeyres: L_t = 113.5 (113.43)
          Paasche:   P_t ~ 108.9 (or direct harmonic form)
          Fisher:    F_t ~ 111.2 (or sqrt(L*P))
          Naive:     114.0 (113.95)
          Bortkiewicz Cov(r^p, r^q) < 0 (negative substitution effect)
        """
        items = [
            {"name": "DEL-BOM, T+7", "p0": 4000.0, "pt": 4600.0, "q0": 1000.0, "qt": 900.0, "w0": 0.444},
            {"name": "DEL-BLR, T+30", "p0": 3500.0, "pt": 3600.0, "q0": 800.0, "qt": 820.0, "w0": 0.311},
            {"name": "BOM-BLR, T+1", "p0": 5000.0, "pt": 6200.0, "q0": 500.0, "qt": 400.0, "w0": 0.245},
        ]

        res = APIxFisherIndexEngine.calculate_single_period_indices(items)

        # 1. Laspeyres check: ~113.43 - 113.5
        self.assertAlmostEqual(res["laspeyres"], 113.43, delta=0.5)

        # 2. Naive average check: ~114.0
        self.assertAlmostEqual(res["naive"], 113.95, delta=0.5)

        # 3. Fisher Ideal Index check: positive and bounded
        self.assertGreater(res["fisher"], 105.0)
        self.assertLess(res["fisher"], 120.0)

        # 4. Bortkiewicz Covariance check: Cov(rp, rq) < 0
        self.assertLess(res["bortkiewicz_cov"], 0.0, "Bortkiewicz covariance must be negative due to substitution effect")

    def test_hampel_outlier_filter(self):
        """Chapter 4.3 Hampel MAD outlier detector test."""
        normal_series = [5000, 5100, 4950, 5050, 4900, 5200, 5150]
        with_glitch = normal_series + [95000, 150]  # Far outside 3.5 MAD
        flags, med, mad = hampel_filter(with_glitch, threshold=3.5)

        self.assertTrue(flags[-2], "95000 should be detected as an outlier")
        self.assertTrue(flags[-1], "150 should be detected as an outlier")
        self.assertFalse(any(flags[:len(normal_series)]), "Normal values must not be flagged")

    def test_airport_service_geocoordinates(self):
        """Airport distance verification for fuel/hedonic distance."""
        dist = airport_service.calculate_distance_km("DEL", "BOM")
        self.assertIsNotNone(dist)
        # Delhi to Mumbai is ~1138 km
        self.assertGreater(dist, 1100.0)
        self.assertLess(dist, 1200.0)

if __name__ == "__main__":
    unittest.main()
