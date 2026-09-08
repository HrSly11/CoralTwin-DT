"""Contract tests for deterministic operational inference inputs and predictions."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from operational.inference import (
    BASELINE_FEATURES,
    InferenceEngine,
    build_feature_vector,
)
from operational.noaa_adapter import ProductObservation
from operational.repository import LatestState, Station
from operational.stations import StationBaseline


def baseline() -> StationBaseline:
    return StationBaseline(BASELINE_FEATURES, (12.5, 28.1, 0.4, 1.0, 8.1, 3.8, 0.7, 1000.0, 2.5, 35.0), "2024-01-01")


def observation(product: str, value: float, observed_at: datetime, dataset_id: str) -> ProductObservation:
    return ProductObservation(
        station_id="station-01",
        product=product,
        observed_at=observed_at,
        requested_latitude=18.25,
        requested_longitude=-87.8,
        returned_latitude=18.25,
        returned_longitude=-87.8,
        value=value,
        unit="degree_C",
        source="noaa_crw_erddap",
        dataset_id=dataset_id,
        request_url="https://example.test/query",
        accessed_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
    )


class InputVectorTests(unittest.TestCase):
    def test_replaces_only_sst_and_dhw_and_keeps_product_provenance_independent(self) -> None:
        state = LatestState(
            station=Station("station-01", "Mesoamerican_Fore_01", 18.25, -87.8),
            sst=observation("sst", 29.4, datetime(2026, 8, 27, tzinfo=timezone.utc), "noaacrwsstDaily"),
            dhw=observation("dhw", 8.5, datetime(2026, 8, 28, tzinfo=timezone.utc), "noaacrwdhwDaily"),
        )

        vector = build_feature_vector(baseline(), state)

        self.assertEqual(BASELINE_FEATURES, vector.feature_names)
        self.assertEqual((12.5, 29.4, 0.4, 8.5, 8.1, 3.8, 0.7, 1000.0, 2.5, 35.0), vector.values)
        self.assertEqual("noaa_crw_erddap", vector.provenance["SST_degC"]["source"])
        self.assertEqual("2026-08-27T00:00:00+00:00", vector.provenance["SST_degC"]["observed_at"])
        self.assertEqual("noaacrwdhwDaily", vector.provenance["DHW_degC_weeks"]["dataset_id"])
        self.assertEqual("static_baseline", vector.provenance["pH_total"]["source"])

    def test_without_noaa_state_uses_all_baseline_values_and_date(self) -> None:
        vector = build_feature_vector(baseline(), None)

        self.assertEqual(baseline().values, vector.values)
        self.assertEqual("static_baseline", vector.provenance["SST_degC"]["source"])
        self.assertEqual("2024-01-01", vector.provenance["SST_degC"]["source_date"])


class _Scaler:
    n_features_in_ = 10

    def transform(self, values):
        return values


class _Classifier:
    n_features_in_ = 10
    classes_ = [0, 1, 2]

    def predict(self, values):
        return [2]

    def predict_proba(self, values):
        return [[0.05, 0.15, 0.8]]


class _Regressor:
    n_features_in_ = 10

    def predict(self, values):
        return [12.5]


class _RecordingScaler(_Scaler):
    def transform(self, values):
        return [[value + 1000.0 for value in values[0]]]


class _RecordingClassifier(_Classifier):
    def __init__(self):
        self.received = []

    def predict(self, values):
        self.received.append(values)
        return super().predict(values)


class _RecordingRegressor(_Regressor):
    def __init__(self):
        self.received = []

    def predict(self, values):
        self.received.append(values)
        return super().predict(values)


def compatible_loader(path: str):
    return {
        "feature_scaler.joblib": _Scaler(),
        "xgboost_classifier.joblib": _Classifier(),
        "xgboost_regressor.joblib": _Regressor(),
    }[Path(path).name]


class InferenceEngineTests(unittest.TestCase):
    def test_xgboost_contract_sends_raw_canonical_vector_to_both_models(self) -> None:
        classifier = _RecordingClassifier()
        regressor = _RecordingRegressor()

        def loader(path: str):
            return {
                "feature_scaler.joblib": _RecordingScaler(),
                "xgboost_classifier.joblib": classifier,
                "xgboost_regressor.joblib": regressor,
            }[Path(path).name]

        result = InferenceEngine(loader=loader).infer(baseline(), None)

        self.assertEqual("ok", result.status)
        expected = [[list(baseline().values)]]
        self.assertEqual(expected, classifier.received)
        self.assertEqual(expected, regressor.received)

    def test_scaled_contract_sends_scaled_vector_to_both_models(self) -> None:
        classifier = _RecordingClassifier()
        regressor = _RecordingRegressor()

        with tempfile.TemporaryDirectory() as temporary_directory:
            contract_path = Path(temporary_directory) / "preprocessing_contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "feature_order": list(BASELINE_FEATURES),
                        "models": {
                            "classifier": {"input_space": "scaled"},
                            "regressor": {"input_space": "scaled"},
                        },
                    }
                ),
                encoding="utf-8",
            )

            def loader(path: str):
                return {
                    "feature_scaler.joblib": _RecordingScaler(),
                    "xgboost_classifier.joblib": classifier,
                    "xgboost_regressor.joblib": regressor,
                }[Path(path).name]

            result = InferenceEngine(
                loader=loader, artifact_paths={"preprocessing_contract": contract_path}
            ).infer(baseline(), None)

        self.assertEqual("ok", result.status)
        expected = [[[value + 1000.0 for value in baseline().values]]]
        self.assertEqual(expected, classifier.received)
        self.assertEqual(expected, regressor.received)

    def test_invalid_contract_returns_unavailable_instead_of_guessing_preprocessing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            contract_path = Path(temporary_directory) / "preprocessing_contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "feature_order": list(BASELINE_FEATURES),
                        "models": {
                            "classifier": {"input_space": "raw"},
                            "regressor": {"input_space": "scaled"},
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = InferenceEngine(
                loader=compatible_loader, artifact_paths={"preprocessing_contract": contract_path}
            ).infer(baseline(), None)

        self.assertEqual("unavailable", result.status)
        self.assertIn("preprocessing contract", result.reason)
        self.assertIn("same input_space", result.reason)

    def test_missing_contract_returns_unavailable_with_clear_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_contract = Path(temporary_directory) / "missing_contract.json"
            result = InferenceEngine(
                loader=compatible_loader, artifact_paths={"preprocessing_contract": missing_contract}
            ).infer(baseline(), None)

        self.assertEqual("unavailable", result.status)
        self.assertIn("preprocessing contract is missing", result.reason)

    def test_missing_artifacts_return_unavailable_without_raising(self) -> None:
        def missing_loader(path: str):
            raise FileNotFoundError(path)

        result = InferenceEngine(loader=missing_loader).infer(baseline(), None)

        self.assertEqual("unavailable", result.status)
        self.assertIn("artifact", result.reason.lower())
        json.dumps(result.to_dict())

    def test_incompatible_feature_count_returns_unavailable(self) -> None:
        class IncompatibleClassifier(_Classifier):
            n_features_in_ = 16

        def loader(path: str):
            if Path(path).name == "xgboost_classifier.joblib":
                return IncompatibleClassifier()
            return compatible_loader(path)

        result = InferenceEngine(loader=loader).infer(baseline(), None)

        self.assertEqual("unavailable", result.status)
        self.assertIn("10", result.reason)

    def test_compatible_artifacts_return_label_confidence_loss_and_json_safe_values(self) -> None:
        result = InferenceEngine(loader=compatible_loader).infer(baseline(), None)

        self.assertEqual("ok", result.status)
        self.assertEqual("High", result.classification)
        self.assertEqual(0.8, result.confidence)
        self.assertEqual(12.5, result.coral_cover_loss_pct)
        self.assertEqual("static_baseline", result.input_provenance["SST_degC"]["source"])
        json.dumps(result.to_dict())


if __name__ == "__main__":
    unittest.main()
