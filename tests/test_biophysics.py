"""
CoralTwin-DT: Automated Biophysical & Model Unit Test Suite
==========================================================
Verifies mathematical bounds, thermodynamic constraints, data integrity,
and deterministic ML predictive performance using standard Python unittest.

Author: CoralTwin-DT Quality Assurance & Test Engineering Lead
License: MIT
"""

import os
import unittest
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, r2_score
import xgboost as xgb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_CSV = os.path.join(PROJECT_ROOT, "03_Data", "final_dataset.csv")
DICT_CSV = os.path.join(PROJECT_ROOT, "03_Data", "data_dictionary_final.csv")


class TestCoralTwinBiophysicsAndModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(DATA_CSV):
            raise FileNotFoundError(f"Dataset not found: {DATA_CSV}")
        cls.df = pd.read_csv(DATA_CSV)

    def test_01_dataset_dimensions_and_nulls(self):
        """Asserts dataset has exactly 15,000 records, 34 columns, and zero null values."""
        self.assertEqual(len(self.df), 15000, f"Expected 15,000 rows, got {len(self.df)}")
        self.assertEqual(self.df.shape[1], 34, f"Expected 34 columns, got {self.df.shape[1]}")
        self.assertEqual(self.df.isnull().sum().sum(), 0, "Dataset contains unexpected null values")

    def test_02_oceanographic_bounds(self):
        """Asserts physical SST, DHW, and salinity fall within realistic oceanic bounds."""
        self.assertGreaterEqual(self.df["SST_degC"].min(), 20.0, "SST below tropical minimum")
        self.assertLessEqual(self.df["SST_degC"].max(), 35.0, "SST exceeds tropical maximum")
        self.assertGreaterEqual(self.df["DHW_degC_weeks"].min(), 0.0, "DHW cannot be negative")
        self.assertLessEqual(self.df["DHW_degC_weeks"].max(), 25.0, "DHW exceeds plausible heatwave threshold")
        self.assertTrue(self.df["Salinity_PSU"].between(30.0, 45.0).all(), "Salinity outside oceanic range")

    def test_03_carbonate_chemistry_bounds(self):
        """Asserts seawater pH and aragonite saturation follow thermodynamic equilibria."""
        self.assertTrue(self.df["pH_total"].between(7.50, 8.35).all(), "pH total scale out of marine bounds")
        self.assertTrue(self.df["Aragonite_Saturation_Omega"].between(1.20, 5.0).all(), "Aragonite saturation out of bounds")

    def test_04_benthic_cover_conservation(self):
        """Asserts sum of live coral, macroalgae, and turf does not exceed 100%."""
        total_benthic = self.df["Live_Coral_Cover_Pct"] + self.df["Macroalgae_Cover_Pct"] + self.df["Turf_Algae_Cover_Pct"]
        self.assertTrue(np.allclose(total_benthic, 100.0, atol=0.01), "Benthic substrate fractions do not sum to 100%")

    def test_05_provenance_and_attribution(self):
        """Asserts metadata compliance with FAIR data principles and attribution tag."""
        self.assertEqual(set(self.df["Data_Source_Type"].unique()), {"Real_Observation_Calibrated", "Digital_Twin_Simulated"})
        self.assertTrue((self.df["Scientific_Attribution"] == "Resultado obtenido mediante prototipo computacional del gemelo digital").all())

    def test_06_xgboost_reproducibility(self):
        """Verifies that the predictive XGBoost model achieves target accuracy (>90%) and R2 (>0.90)."""
        features = [
            "Depth_m", "SST_degC", "SST_Anomaly_degC", "HotSpot_degC", "DHW_degC_weeks",
            "pH_total", "Salinity_PSU", "Dissolved_Oxygen_mg_L", "Aragonite_Saturation_Omega",
            "Turbidity_NTU", "Kd_490_m_inv", "PAR_umol_m2_s", "Structural_Rugosity",
            "Live_Coral_Cover_Pct", "Macroalgae_Cover_Pct", "Shannon_Diversity_H"
        ]
        X = self.df[features].values
        y_class = self.df["Bleaching_Risk"].map({"Low": 0, "Medium": 1, "High": 2}).values
        y_reg = self.df["Coral_Cover_Loss_Pct"].values

        clf = xgb.XGBClassifier(n_estimators=50, max_depth=4, learning_rate=0.1, random_state=42, eval_metric="mlogloss")
        clf.fit(X[:12000], y_class[:12000])
        preds = clf.predict(X[12000:])
        acc = accuracy_score(y_class[12000:], preds)
        self.assertGreaterEqual(acc, 0.90, f"XGBoost classification accuracy {acc:.4f} fell below 0.90")

        reg = xgb.XGBRegressor(n_estimators=50, max_depth=4, learning_rate=0.1, random_state=42)
        reg.fit(X[:12000], y_reg[:12000])
        preds_r = reg.predict(X[12000:])
        r2 = r2_score(y_reg[12000:], preds_r)
        self.assertGreaterEqual(r2, 0.90, f"XGBoost regression R2 {r2:.4f} fell below 0.90")


if __name__ == "__main__":
    unittest.main()
