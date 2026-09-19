from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "workshop_id",
    "area",
    "inspection_date",
    "wiring_condition_score",
    "equipment_load_pct",
    "panel_condition_score",
    "grounding_score",
    "extension_cord_score",
    "moisture_exposure_score",
    "equipment_age_years",
    "incident_count_90d",
    "inspection_image_signal_score",
    "workshop_occupancy",
]

NUMERIC_COLUMNS = [
    "wiring_condition_score",
    "equipment_load_pct",
    "panel_condition_score",
    "grounding_score",
    "extension_cord_score",
    "moisture_exposure_score",
    "equipment_age_years",
    "incident_count_90d",
    "inspection_image_signal_score",
    "workshop_occupancy",
]


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return float(np.clip(value, low, high))


def _risk_from_good(score: pd.Series) -> pd.Series:
    return (100 - pd.to_numeric(score, errors="coerce").fillna(50)).clip(0, 100)


def _scale_series(series: pd.Series, low: float, high: float) -> pd.Series:
    return ((pd.to_numeric(series, errors="coerce") - low) / (high - low) * 100).clip(0, 100).fillna(0)


def classify(score: float) -> str:
    score = float(score)
    if score >= 75:
        return "Critical"
    if score >= 55:
        return "High"
    if score >= 35:
        return "Moderate"
    return "Low"


def validate_dataframe(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    validate_dataframe(df)
    out = df.copy()
    out["inspection_date"] = pd.to_datetime(out["inspection_date"], errors="coerce")
    for col in NUMERIC_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in NUMERIC_COLUMNS:
        if col not in out.columns:
            out[col] = 0.0
    out[NUMERIC_COLUMNS] = out[NUMERIC_COLUMNS].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return add_screening_metrics(out)


def add_screening_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    wiring_risk = _risk_from_good(out["wiring_condition_score"])
    panel_risk = _risk_from_good(out["panel_condition_score"])
    grounding_risk = _risk_from_good(out["grounding_score"])
    extension_risk = _risk_from_good(out["extension_cord_score"])
    load_risk = _scale_series(out["equipment_load_pct"], 40, 120)
    moisture_risk = pd.to_numeric(out["moisture_exposure_score"], errors="coerce").fillna(0).clip(0, 100)
    age_risk = _scale_series(out["equipment_age_years"], 0, 20)
    incident_risk = _scale_series(out["incident_count_90d"], 0, 8)
    image_signal = pd.to_numeric(out["inspection_image_signal_score"], errors="coerce").fillna(0).clip(0, 100)

    out["wiring_risk"] = wiring_risk
    out["load_risk"] = load_risk
    out["panel_risk"] = panel_risk
    out["grounding_risk"] = grounding_risk
    out["extension_risk"] = extension_risk
    out["moisture_risk"] = moisture_risk
    out["age_risk"] = age_risk
    out["incident_risk"] = incident_risk
    out["image_signal_risk"] = image_signal

    weights = {
        "wiring_risk": 0.18,
        "load_risk": 0.16,
        "panel_risk": 0.13,
        "grounding_risk": 0.13,
        "extension_risk": 0.11,
        "moisture_risk": 0.10,
        "age_risk": 0.06,
        "incident_risk": 0.08,
        "image_signal_risk": 0.05,
    }
    score = sum(out[k] * w for k, w in weights.items())
    out["electrical_hazard_screening_score"] = score.clip(0, 100).round(1)
    out["hazard_class"] = out["electrical_hazard_screening_score"].map(classify)

    components = out[list(weights)]
    out["dominant_driver"] = components.idxmax(axis=1).map({
        "wiring_risk": "Wiring condition",
        "load_risk": "Equipment load",
        "panel_risk": "Panel condition",
        "grounding_risk": "Grounding",
        "extension_risk": "Extension cords",
        "moisture_risk": "Moisture exposure",
        "age_risk": "Equipment age",
        "incident_risk": "Recent incidents",
        "image_signal_risk": "Inspection image signal",
    })

    out["review_flag"] = np.select(
        [
            out["electrical_hazard_screening_score"] >= 75,
            out["electrical_hazard_screening_score"] >= 55,
            out["electrical_hazard_screening_score"] >= 35,
        ],
        ["Immediate engineering review", "Priority inspection review", "Routine corrective review"],
        default="Monitor",
    )
    return out


def summary_metrics(df: pd.DataFrame) -> Dict[str, float]:
    score = df["electrical_hazard_screening_score"]
    return {
        "workshops": int(df["workshop_id"].nunique()),
        "avg_score": round(float(score.mean()), 1),
        "high_or_critical": int(df["hazard_class"].isin(["High", "Critical"]).sum()),
        "critical": int((df["hazard_class"] == "Critical").sum()),
        "avg_load": round(float(df["equipment_load_pct"].mean()), 1),
        "avg_incidents": round(float(df["incident_count_90d"].mean()), 1),
    }


def driver_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    order = [
        "Wiring condition", "Equipment load", "Panel condition", "Grounding",
        "Extension cords", "Moisture exposure", "Equipment age", "Recent incidents",
        "Inspection image signal"
    ]
    s = df["dominant_driver"].value_counts().reindex(order).fillna(0).astype(int)
    return s.rename_axis("driver").reset_index(name="workshops")


def area_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("area", as_index=False)
        .agg(
            workshops=("workshop_id", "nunique"),
            avg_score=("electrical_hazard_screening_score", "mean"),
            high_or_critical=("hazard_class", lambda s: int(s.isin(["High", "Critical"]).sum())),
            avg_load=("equipment_load_pct", "mean"),
            avg_incidents=("incident_count_90d", "mean"),
        )
        .sort_values("avg_score", ascending=False)
    )


def scenario_score(
    base_row: pd.Series,
    *,
    load_change_pct: float = 0.0,
    wiring_delta: float = 0.0,
    grounding_delta: float = 0.0,
    moisture_delta: float = 0.0,
    extension_delta: float = 0.0,
    incident_delta: int = 0,
) -> Dict[str, float | str]:
    row = base_row.copy()
    row["equipment_load_pct"] = float(row["equipment_load_pct"]) + load_change_pct
    row["wiring_condition_score"] = clamp(float(row["wiring_condition_score"]) + wiring_delta)
    row["grounding_score"] = clamp(float(row["grounding_score"]) + grounding_delta)
    row["moisture_exposure_score"] = clamp(float(row["moisture_exposure_score"]) + moisture_delta)
    row["extension_cord_score"] = clamp(float(row["extension_cord_score"]) + extension_delta)
    row["incident_count_90d"] = max(0, int(row["incident_count_90d"]) + int(incident_delta))
    mini = pd.DataFrame([row])
    scored = add_screening_metrics(mini).iloc[0]
    return {
        "score": float(scored["electrical_hazard_screening_score"]),
        "class": str(scored["hazard_class"]),
        "driver": str(scored["dominant_driver"]),
    }


def analyze_inspection_image(image_bytes: bytes) -> Dict[str, float | str]:
    """Local-only visual signal extraction. This is not a vision model or an electrical diagnosis."""
    try:
        from PIL import Image
        from io import BytesIO

        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        arr = np.asarray(image).astype(np.float32) / 255.0
        gray = arr.mean(axis=2)
        brightness = float(gray.mean())
        contrast = float(gray.std())
        red_dominance = float(np.clip(arr[:, :, 0].mean() - arr[:, :, 1].mean(), -1, 1))
        gx = np.diff(gray, axis=1)
        gy = np.diff(gray, axis=0)
        edge_density = float((np.abs(gx).mean() + np.abs(gy).mean()) / 2)
        # Visual signal is deliberately generic: it identifies unusual visual texture/contrast only.
        score = 100 * (
            0.35 * np.clip(abs(brightness - 0.55) / 0.55, 0, 1)
            + 0.35 * np.clip(contrast / 0.28, 0, 1)
            + 0.20 * np.clip(edge_density / 0.14, 0, 1)
            + 0.10 * np.clip(max(red_dominance, 0) / 0.20, 0, 1)
        )
        return {
            "visual_signal_score": round(clamp(score), 1),
            "brightness": round(brightness * 100, 1),
            "contrast": round(contrast * 100, 1),
            "edge_density": round(edge_density * 100, 2),
            "note": "Generic local visual-anomaly signal; not a certified electrical hazard detector.",
        }
    except Exception as exc:  # pragma: no cover - defensive path
        raise ValueError(f"Could not analyze image locally: {exc}") from exc
