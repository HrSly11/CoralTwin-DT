"""Deterministic model inference over static station and NOAA observations."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping

from .repository import LatestState
from .stations import BASELINE_FEATURES, StationBaseline


CLASS_LABELS: tuple[str, ...] = ("Low", "Medium", "High")
CORAL_COVER_LOSS_RANGE = (0.0, 95.0)

_DEFAULT_ARTIFACT_PATHS: dict[str, str] = {
    "scaler": str(
        Path(__file__).resolve().parents[1]
        / "06_AI_and_Modeling"
        / "machine_learning"
        / "saved_models"
        / "feature_scaler.joblib"
    ),
    "classifier": str(
        Path(__file__).resolve().parents[1]
        / "06_AI_and_Modeling"
        / "machine_learning"
        / "saved_models"
        / "xgboost_classifier.joblib"
    ),
    "regressor": str(
        Path(__file__).resolve().parents[1]
        / "06_AI_and_Modeling"
        / "machine_learning"
        / "saved_models"
        / "xgboost_regressor.joblib"
    ),
    "contract": str(
        Path(__file__).resolve().parents[1]
        / "06_AI_and_Modeling"
        / "machine_learning"
        / "saved_models"
        / "preprocessing_contract.json"
    ),
}


class InferenceInputError(ValueError):
    """Raised when a baseline or operational state cannot form a feature vector."""


@dataclass(frozen=True)
class PreprocessingContract:
    """Explicit feature-space declaration shared by deployed prediction models."""

    input_space: str
    feature_names: tuple[str, ...]


def _load_preprocessing_contract(path: str) -> PreprocessingContract:
    """Read and validate the model bundle's declared preprocessing contract."""

    try:
        with Path(path).open(encoding="utf-8") as handle:
            document = json.load(handle)
    except FileNotFoundError as exc:
        raise ValueError(f"preprocessing contract is missing at {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"preprocessing contract cannot be read at {path}: {exc}") from exc

    if not isinstance(document, Mapping):
        raise ValueError("preprocessing contract must be a JSON object")
    if document.get("schema_version") != 1:
        raise ValueError("preprocessing contract has an unsupported schema_version")

    feature_names = document.get("feature_order")
    if not isinstance(feature_names, list) or not all(isinstance(feature, str) for feature in feature_names):
        raise ValueError("preprocessing contract must declare feature_order as a string list")
    if tuple(feature_names) != BASELINE_FEATURES:
        raise ValueError("preprocessing contract feature_order does not match the canonical model features")

    models = document.get("models")
    if not isinstance(models, Mapping):
        raise ValueError("preprocessing contract must declare classifier and regressor models")
    spaces: list[str] = []
    for role in ("classifier", "regressor"):
        declaration = models.get(role)
        if not isinstance(declaration, Mapping):
            raise ValueError(f"preprocessing contract is missing the {role} declaration")
        space = declaration.get("input_space")
        if space not in {"raw", "scaled"}:
            raise ValueError(f"preprocessing contract has an invalid {role} input_space")
        spaces.append(space)
    if spaces[0] != spaces[1]:
        raise ValueError("preprocessing contract must use the same input_space for classifier and regressor")

    return PreprocessingContract(input_space=spaces[0], feature_names=tuple(feature_names))


@dataclass(frozen=True)
class FeatureVector:
    """Ordered model input and provenance for each feature."""

    feature_names: tuple[str, ...]
    values: tuple[float, ...]
    provenance: Mapping[str, Mapping[str, Any]]

    @property
    def feature_values(self) -> tuple[float, ...]:
        return self.values

    @property
    def input_provenance(self) -> Mapping[str, Mapping[str, Any]]:
        return self.provenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_names": self.feature_names,
            "values": self.values,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class InferenceResult:
    """JSON-safe inference response, including explicit unavailable failures."""

    status: str
    classification: str | None
    confidence: float | None
    coral_cover_loss_pct: float | None
    artifact_paths: Mapping[str, str]
    input_provenance: Mapping[str, Mapping[str, Any]]
    reason: str | None = None

    @property
    def label(self) -> str | None:
        return self.classification

    @property
    def regression(self) -> float | None:
        return self.coral_cover_loss_pct

    @property
    def loss(self) -> float | None:
        return self.coral_cover_loss_pct

    @property
    def available(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "status": self.status,
            "classification": self.classification,
            "confidence": self.confidence,
            "coral_cover_loss_pct": self.coral_cover_loss_pct,
            "regression": self.coral_cover_loss_pct,
            "loss": self.coral_cover_loss_pct,
            "artifact_paths": self.artifact_paths,
            "input_provenance": self.input_provenance,
        }
        if self.reason is not None:
            result["reason"] = self.reason
        return _json_safe(result)


def _json_safe(value: Any) -> Any:
    """Convert common numpy scalar/container values to JSON primitives."""

    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return _json_safe(item())
        except (TypeError, ValueError):
            pass
    return str(value)


def _finite_float(value: Any, description: str) -> float:
    try:
        converted = float(value)
    except (TypeError, ValueError) as exc:
        raise InferenceInputError(f"{description} must be numeric") from exc
    if not math.isfinite(converted):
        raise InferenceInputError(f"{description} must be finite")
    return converted


def _timestamp(value: datetime) -> str:
    return value.isoformat()


def _baseline_mapping(baseline: StationBaseline | Mapping[str, Any]) -> tuple[dict[str, float], str | None]:
    if isinstance(baseline, StationBaseline):
        if tuple(baseline.feature_names) != BASELINE_FEATURES:
            raise InferenceInputError("Station baseline feature order does not match the model contract")
        source_date = baseline.source_date
        raw_values = dict(zip(baseline.feature_names, baseline.values, strict=True))
    elif isinstance(baseline, Mapping):
        source_date = baseline.get("source_date")
        raw_values = {feature: baseline[feature] for feature in BASELINE_FEATURES if feature in baseline}
    else:
        raise InferenceInputError("baseline must be a StationBaseline or feature mapping")

    missing = tuple(feature for feature in BASELINE_FEATURES if feature not in raw_values)
    if missing:
        raise InferenceInputError(f"Baseline is missing features: {', '.join(missing)}")
    values = {feature: _finite_float(raw_values[feature], f"Baseline feature {feature}") for feature in BASELINE_FEATURES}
    return values, None if source_date is None else str(source_date)


def _noaa_provenance(observation: Any) -> dict[str, Any]:
    observed_at = getattr(observation, "observed_at", None)
    if not isinstance(observed_at, datetime):
        raise InferenceInputError("NOAA observation timestamp is invalid")
    dataset_id = getattr(observation, "dataset_id", None)
    if not isinstance(dataset_id, str) or not dataset_id:
        raise InferenceInputError("NOAA observation dataset is invalid")
    source = getattr(observation, "source", "noaa_crw_erddap")
    return {
        "source": str(source),
        "product": str(getattr(observation, "product", "")),
        "observed_at": _timestamp(observed_at),
        "dataset_id": dataset_id,
    }


def build_feature_vector(
    baseline: StationBaseline | Mapping[str, Any], latest_state: LatestState | None
) -> FeatureVector:
    """Build the exact ordered model vector, replacing only current SST/DHW."""

    values, source_date = _baseline_mapping(baseline)
    provenance: dict[str, dict[str, Any]] = {
        feature: {"source": "static_baseline", "source_date": source_date} for feature in BASELINE_FEATURES
    }

    replacements = (("SST_degC", "sst"), ("DHW_degC_weeks", "dhw"))
    for feature, product in replacements:
        observation = getattr(latest_state, product, None) if latest_state is not None else None
        if observation is None:
            continue
        if getattr(observation, "product", None) != product:
            continue
        values[feature] = _finite_float(getattr(observation, "value", None), f"NOAA {product} value")
        provenance[feature] = _noaa_provenance(observation)

    return FeatureVector(BASELINE_FEATURES, tuple(values[feature] for feature in BASELINE_FEATURES), provenance)


# Names that read naturally at call sites and preserve one implementation.
build_ordered_feature_vector = build_feature_vector
build_inference_inputs = build_feature_vector


Loader = Callable[[str], Any]


def _default_loader(path: str) -> Any:
    import joblib

    return joblib.load(path)


def _first(value: Any) -> Any:
    """Read one scalar from a model's one-sample array without requiring numpy."""

    item = getattr(value, "item", None)
    if callable(item):
        try:
            return item()
        except (TypeError, ValueError):
            pass
    if isinstance(value, (str, bytes)):
        return value
    try:
        if len(value) == 0:
            raise ValueError("model returned no values")
        return _first(value[0])
    except TypeError:
        return value


def _row(value: Any) -> Any:
    try:
        return value[0]
    except (IndexError, KeyError, TypeError):
        return value


class InferenceEngine:
    """Load saved artifacts and provide a non-throwing inference boundary."""

    def __init__(self, loader: Loader | None = None, artifact_paths: Mapping[str, str | Path] | None = None) -> None:
        self._loader = loader or _default_loader
        paths = dict(_DEFAULT_ARTIFACT_PATHS)
        if artifact_paths:
            for key, value in artifact_paths.items():
                canonical = {
                    "feature_scaler": "scaler",
                    "xgboost_classifier": "classifier",
                    "xgboost_regressor": "regressor",
                    "preprocessing_contract": "contract",
                }.get(key, key)
                if canonical not in paths:
                    raise ValueError(f"Unknown inference artifact key: {key}")
                paths[canonical] = str(value)
        self._artifact_paths = paths

    @property
    def artifact_paths(self) -> Mapping[str, str]:
        return self._artifact_paths

    def _unavailable(self, reason: str, provenance: Mapping[str, Mapping[str, Any]] | None = None) -> InferenceResult:
        return InferenceResult(
            status="unavailable",
            classification=None,
            confidence=None,
            coral_cover_loss_pct=None,
            artifact_paths=self._artifact_paths,
            input_provenance=provenance or {},
            reason=reason,
        )

    @staticmethod
    def _validate_artifact_features(artifacts: Mapping[str, Any]) -> None:
        for name, artifact in artifacts.items():
            if not hasattr(artifact, "n_features_in_"):
                continue
            try:
                count = int(getattr(artifact, "n_features_in_"))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{name} artifact reports an invalid feature count") from exc
            if count != len(BASELINE_FEATURES):
                raise ValueError(f"{name} artifact expects {count} features; expected {len(BASELINE_FEATURES)}")

    @staticmethod
    def _label(prediction: Any, classifier: Any) -> tuple[str, int]:
        raw = _first(prediction)
        classes = getattr(classifier, "classes_", None)
        if classes is not None:
            classes_list = list(classes)
            if raw in classes_list:
                index = classes_list.index(raw)
                if index < len(CLASS_LABELS):
                    return CLASS_LABELS[index], index
        if isinstance(raw, str) and raw in CLASS_LABELS:
            return raw, CLASS_LABELS.index(raw)
        try:
            index = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"classifier returned unsupported label {raw!r}") from exc
        if index < 0 or index >= len(CLASS_LABELS):
            raise ValueError(f"classifier returned unsupported class index {index}")
        return CLASS_LABELS[index], index

    @staticmethod
    def _confidence(classifier: Any, matrix: Any, class_index: int) -> float | None:
        predict_proba = getattr(classifier, "predict_proba", None)
        if not callable(predict_proba):
            return None
        probabilities = list(_row(predict_proba(matrix)))
        if not probabilities:
            raise ValueError("classifier returned no probabilities")
        converted = [_finite_float(value, "classification probability") for value in probabilities]
        if any(value < 0.0 or value > 1.0 for value in converted):
            raise ValueError("classifier returned a probability outside [0, 1]")
        if class_index >= len(converted):
            raise ValueError("classifier probability vector does not contain the predicted class")
        return converted[class_index]

    def infer(
        self, baseline: StationBaseline | Mapping[str, Any], latest_state: LatestState | None
    ) -> InferenceResult:
        try:
            vector = build_feature_vector(baseline, latest_state)
        except Exception as exc:
            return self._unavailable(f"invalid inference inputs: {exc}")

        try:
            contract = _load_preprocessing_contract(self._artifact_paths["contract"])
            artifacts = {
                "classifier": self._loader(self._artifact_paths["classifier"]),
                "regressor": self._loader(self._artifact_paths["regressor"]),
            }
            if contract.input_space == "scaled":
                artifacts["scaler"] = self._loader(self._artifact_paths["scaler"])
            self._validate_artifact_features(artifacts)
            matrix: Any = [list(vector.values)]
            if contract.input_space == "scaled":
                transform = getattr(artifacts["scaler"], "transform")
                if not callable(transform):
                    raise ValueError("scaled preprocessing contract requires a scaler transform method")
                matrix = transform(matrix)
            classifier = artifacts["classifier"]
            regressor = artifacts["regressor"]
            classification, class_index = self._label(classifier.predict(matrix), classifier)
            confidence = self._confidence(classifier, matrix, class_index)
            loss = _finite_float(_first(regressor.predict(matrix)), "regression output")
            lower, upper = CORAL_COVER_LOSS_RANGE
            if not lower <= loss <= upper:
                raise ValueError(f"regression output {loss} is outside [{lower}, {upper}]")
        except Exception as exc:
            return self._unavailable(f"model artifacts unavailable or incompatible: {exc}", vector.provenance)

        return InferenceResult(
            status="ok",
            classification=classification,
            confidence=confidence,
            coral_cover_loss_pct=loss,
            artifact_paths=self._artifact_paths,
            input_provenance=vector.provenance,
        )

    predict = infer
    run = infer


__all__ = [
    "BASELINE_FEATURES",
    "CLASS_LABELS",
    "CORAL_COVER_LOSS_RANGE",
    "FeatureVector",
    "InferenceEngine",
    "InferenceInputError",
    "InferenceResult",
    "PreprocessingContract",
    "build_feature_vector",
    "build_inference_inputs",
    "build_ordered_feature_vector",
]
