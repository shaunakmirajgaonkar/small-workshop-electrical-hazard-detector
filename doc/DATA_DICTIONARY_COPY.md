# Data Dictionary

| Column | Type | Meaning | Suggested range |
|---|---|---|---|
| workshop_id | string | Unique workshop record ID | unique text |
| area | string | Workshop area or activity | text |
| inspection_date | date | Inspection/assessment date | YYYY-MM-DD |
| wiring_condition_score | number | Condition score where higher means better | 0–100 |
| equipment_load_pct | number | Estimated equipment load | 0–150% |
| panel_condition_score | number | Electrical panel condition score | 0–100 |
| grounding_score | number | Grounding-condition score | 0–100 |
| extension_cord_score | number | Extension-cord condition score | 0–100 |
| moisture_exposure_score | number | Moisture exposure pressure | 0–100 |
| equipment_age_years | number | Typical age of major equipment | 0+ |
| incident_count_90d | integer | Reported electrical incidents in previous 90 days | 0+ |
| inspection_image_signal_score | number | Locally supplied generic visual signal | 0–100 |
| workshop_occupancy | integer | Typical people present during operation | 0+ |
