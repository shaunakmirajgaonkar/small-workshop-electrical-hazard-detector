import pandas as pd

from analytics import REQUIRED_COLUMNS, classify, prepare_data, scenario_score, analyze_inspection_image


def sample():
    return pd.DataFrame([
        {
            "workshop_id":"W1","area":"Test","inspection_date":"2026-09-01",
            "wiring_condition_score":40,"equipment_load_pct":110,"panel_condition_score":45,
            "grounding_score":35,"extension_cord_score":45,"moisture_exposure_score":50,
            "equipment_age_years":12,"incident_count_90d":4,"inspection_image_signal_score":25,
            "workshop_occupancy":8,
        },
        {
            "workshop_id":"W2","area":"Test","inspection_date":"2026-09-02",
            "wiring_condition_score":90,"equipment_load_pct":60,"panel_condition_score":88,
            "grounding_score":92,"extension_cord_score":90,"moisture_exposure_score":10,
            "equipment_age_years":3,"incident_count_90d":0,"inspection_image_signal_score":5,
            "workshop_occupancy":3,
        },
    ])


def test_required_columns_present():
    df = sample()
    assert all(c in df.columns for c in REQUIRED_COLUMNS)


def test_prepare_data_adds_score_and_class():
    out = prepare_data(sample())
    assert "electrical_hazard_screening_score" in out.columns
    assert "hazard_class" in out.columns
    assert out["electrical_hazard_screening_score"].between(0, 100).all()
    assert set(out["hazard_class"]).issubset({"Low","Moderate","High","Critical"})


def test_scenario_changes_score():
    out = prepare_data(sample())
    row = out.iloc[0]
    baseline = float(row["electrical_hazard_screening_score"])
    scenario = scenario_score(row, load_change_pct=20, wiring_delta=-20)
    assert float(scenario["score"]) >= baseline


def test_classify_boundaries():
    assert classify(20) == "Low"
    assert classify(40) == "Moderate"
    assert classify(60) == "High"
    assert classify(80) == "Critical"
