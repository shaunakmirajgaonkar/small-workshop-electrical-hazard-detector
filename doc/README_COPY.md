# Small-Workshop Electrical Hazard Detector

A 100% local-first Streamlit dashboard for screening electrical-safety signals in small workshops using locally supplied inspection records and optional local inspection images.

## What it analyzes
- Wiring condition
- Equipment load
- Panel condition
- Grounding
- Extension-cord condition
- Moisture exposure
- Equipment age
- Recent incident count
- Workshop occupancy
- Optional local inspection-image visual signal

## Dashboard
Overview • Risk Matrix • Electrical Systems • Incidents & Load • Workshop Profiles • Priority Queue • Scenario Lab • Image Review • Reports & Export • Data Explorer

## Local-first design
No external APIs, cloud inference, satellite services, or remote image services are required. CSV data stays local. Image review uses a simple local visual-signal heuristic and is explicitly not a certified electrical inspection or computer-vision diagnosis.

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -q
streamlit run app.py
```

## Data
Use `data/sample_workshop_electrical.csv` for demonstration and `data/workshop_electrical_template.csv` for new records.

## Responsible use
The screening score is an explainable prioritization aid. It does not establish an electrical violation, guarantee safety, replace a qualified electrician or engineer, or substitute for applicable electrical codes, inspection procedures, or emergency guidance.
