from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics import (
    REQUIRED_COLUMNS,
    add_screening_metrics,
    analyze_inspection_image,
    area_summary,
    driver_breakdown,
    prepare_data,
    scenario_score,
    summary_metrics,
)

st.set_page_config(
    page_title="Workshop Electrical Hazard Detector",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE = Path(__file__).parent
ASSETS = BASE / "assets"
DATA = BASE / "data"

st.markdown(
    """
    <style>
    :root{--ink:#122033;--muted:#5b6b7f;--line:#dce5ef;--card:#ffffff;--bg:#f4f8fc;--accent:#2f80ed;--accent2:#00a6a6;--warn:#f59e0b;--danger:#e45756;}
    .stApp{background:linear-gradient(180deg,#f7fbff 0%,#eef5fb 100%);color:var(--ink);}
    .block-container{padding-top:1.2rem;padding-bottom:2rem;max-width:1500px;}
    h1,h2,h3,h4{color:var(--ink)!important;letter-spacing:-0.02em;}
    .hero{background:linear-gradient(110deg,#ffffff 0%,#edf7ff 55%,#ecfbf8 100%);border:1px solid var(--line);border-radius:24px;padding:28px 30px;margin-bottom:18px;box-shadow:0 12px 35px rgba(34,57,82,.07);}
    .hero-title{font-size:2.15rem;font-weight:800;margin:0 0 6px;}
    .hero-sub{color:var(--muted);font-size:1rem;line-height:1.55;max-width:920px;}
    .chip{display:inline-block;padding:7px 11px;border-radius:999px;background:#e8f2ff;color:#1e5ca8;font-weight:700;font-size:.78rem;margin-right:6px;}
    .metric-card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px 20px;box-shadow:0 8px 22px rgba(34,57,82,.06);min-height:115px;}
    .metric-label{color:var(--muted);font-size:.82rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;}
    .metric-value{font-size:2rem;font-weight:800;color:var(--ink);margin-top:4px;}
    .metric-note{color:#718096;font-size:.8rem;margin-top:2px;}
    .section{background:rgba(255,255,255,.78);border:1px solid var(--line);border-radius:20px;padding:20px;margin:12px 0;}
    .small-note{font-size:.82rem;color:var(--muted);line-height:1.5;}
    .alert{border-radius:14px;padding:12px 15px;border:1px solid #ffd39a;background:#fff9ef;color:#7b5311;margin:8px 0;}
    [data-testid="stSidebar"]{background:linear-gradient(180deg,#fafdff 0%,#eef5fb 100%);border-right:1px solid var(--line);}
    [data-testid="stSidebar"] *{color:var(--ink);}
    .stButton>button,.stDownloadButton>button{border-radius:12px;font-weight:700;border:1px solid #c9d8e8;}
    </style>
    """,
    unsafe_allow_html=True,
)


def svg_data_url(path: Path) -> str:
    raw = path.read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(raw).decode("ascii")


def metric_card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown("## ⚡ Workshop Safety Lab")
    st.caption("LOCAL-FIRST • CSV + OPTIONAL IMAGE REVIEW")
    uploaded = st.file_uploader("Upload workshop inspection CSV", type=["csv"], help="Upload a CSV matching the bundled template.")
    use_sample = st.checkbox("Use bundled sample data", value=uploaded is None)
    page = st.radio(
        "Workspace",
        ["Overview", "Risk Matrix", "Electrical Systems", "Incidents & Load", "Workshop Profiles", "Priority Queue", "Scenario Lab", "Image Review", "Reports & Export", "Data Explorer"],
    )
    st.markdown("---")
    st.markdown("**Scope**")
    st.caption("Local screening only. Review outputs with qualified electrical safety professionals and applicable standards.")

if uploaded is not None and not use_sample:
    df_raw = pd.read_csv(uploaded)
else:
    sample_path = DATA / "sample_workshop_electrical.csv"
    df_raw = pd.read_csv(sample_path)

try:
    df = prepare_data(df_raw)
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

m = summary_metrics(df)

hero_img = svg_data_url(ASSETS / "electrical.svg")
st.markdown(
    f"""
    <div class="hero">
      <div style="display:flex;gap:26px;align-items:center;justify-content:space-between;">
        <div style="flex:1;min-width:0;">
          <div class="chip">100% LOCAL</div><div class="chip">EXPLAINABLE SCREENING</div><div class="chip">WORKSHOP ELECTRICAL SAFETY</div>
          <div class="hero-title">Small-Workshop Electrical Hazard Detector</div>
          <div class="hero-sub">A local analytics workspace for screening electrical-safety signals across wiring condition, equipment load, panels, grounding, extension cords, moisture exposure, equipment age, incident history and optional inspection-image signals.</div>
        </div>
        <img src="{hero_img}" style="width:330px;max-width:34%;border-radius:18px;border:1px solid #dce5ef;"/>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("No records found in the dataset.")
    st.stop()

if page == "Overview":
    st.subheader("Safety overview")
    cols = st.columns(5)
    with cols[0]: metric_card("WORKSHOPS", f"{m['workshops']}", "unique records")
    with cols[1]: metric_card("AVG SCREEN", f"{m['avg_score']}/100", "screening score")
    with cols[2]: metric_card("HIGH + CRITICAL", f"{m['high_or_critical']}", "records flagged")
    with cols[3]: metric_card("CRITICAL", f"{m['critical']}", "highest review band")
    with cols[4]: metric_card("AVG LOAD", f"{m['avg_load']}%", "equipment load signal")

    st.markdown('<div class="section">', unsafe_allow_html=True)
    left, right = st.columns([1.25, 0.75])
    with left:
        fig = px.bar(
            df.sort_values("electrical_hazard_screening_score", ascending=False),
            x="workshop_id", y="electrical_hazard_screening_score", color="hazard_class",
            category_orders={"hazard_class": ["Low", "Moderate", "High", "Critical"]},
            title="Workshop screening profile",
            labels={"electrical_hazard_screening_score":"Screening score","workshop_id":"Workshop"},
        )
        fig.update_layout(height=400, margin=dict(l=10,r=10,t=55,b=10), legend_title_text="Class")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        db = driver_breakdown(df)
        fig2 = px.pie(db, values="workshops", names="driver", hole=.58, title="Dominant screening drivers")
        fig2.update_layout(height=400, margin=dict(l=10,r=10,t=55,b=10), legend_title_text="Driver")
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown("### Review queue snapshot")
    q = df[["workshop_id","area","electrical_hazard_screening_score","hazard_class","dominant_driver","review_flag"]].sort_values("electrical_hazard_screening_score", ascending=False).head(8)
    st.dataframe(q, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Risk Matrix":
    st.subheader("Risk matrix")
    fig = px.scatter(
        df, x="equipment_load_pct", y="electrical_hazard_screening_score", size="workshop_occupancy",
        color="hazard_class", hover_name="workshop_id", hover_data=["area","dominant_driver"],
        labels={"equipment_load_pct":"Equipment load (%)","electrical_hazard_screening_score":"Screening score"},
        title="Equipment load vs electrical screening pressure",
    )
    fig.add_hline(y=55, line_dash="dash", annotation_text="High threshold")
    fig.add_hline(y=75, line_dash="dot", annotation_text="Critical threshold")
    fig.update_layout(height=520, margin=dict(l=10,r=10,t=55,b=10))
    st.plotly_chart(fig, use_container_width=True)

    a, b = st.columns(2)
    with a:
        st.markdown("### Area comparison")
        st.dataframe(area_summary(df).round(1), use_container_width=True, hide_index=True)
    with b:
        st.markdown("### Class distribution")
        counts = df["hazard_class"].value_counts().reindex(["Low","Moderate","High","Critical"]).fillna(0).reset_index()
        counts.columns = ["class","workshops"]
        st.plotly_chart(px.bar(counts, x="class", y="workshops", text_auto=True), use_container_width=True)

elif page == "Electrical Systems":
    st.subheader("Electrical systems deep dive")
    cols = st.columns(3)
    with cols[0]:
        st.metric("Mean wiring condition", f"{df.wiring_condition_score.mean():.1f}/100")
    with cols[1]:
        st.metric("Mean panel condition", f"{df.panel_condition_score.mean():.1f}/100")
    with cols[2]:
        st.metric("Mean grounding condition", f"{df.grounding_score.mean():.1f}/100")

    heat = df[["wiring_risk","panel_risk","grounding_risk","extension_risk","moisture_risk"]].mean().rename(index={
        "wiring_risk":"Wiring","panel_risk":"Panel","grounding_risk":"Grounding","extension_risk":"Extension cords","moisture_risk":"Moisture"})
    fig = px.bar(heat.reset_index(name="risk"), x="index", y="risk", title="Average component risk contribution")
    fig.update_layout(height=390, xaxis_title="Component", yaxis_title="Risk signal (0–100)", margin=dict(l=10,r=10,t=55,b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Component radar for selected workshop")
    selected = st.selectbox("Workshop", df["workshop_id"].astype(str).tolist())
    row = df[df["workshop_id"].astype(str) == selected].iloc[0]
    radar_labels = ["Wiring","Load","Panel","Grounding","Extension","Moisture"]
    radar_values = [row.wiring_risk,row.load_risk,row.panel_risk,row.grounding_risk,row.extension_risk,row.moisture_risk]
    radar_values += radar_values[:1]
    fig = go.Figure(go.Scatterpolar(r=radar_values, theta=radar_labels+[radar_labels[0]], fill="toself", name=selected))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0,100])), height=430, margin=dict(l=20,r=20,t=25,b=20))
    st.plotly_chart(fig, use_container_width=True)

elif page == "Incidents & Load":
    st.subheader("Load and incident signals")
    fig = px.scatter(
        df, x="incident_count_90d", y="equipment_load_pct", size="equipment_age_years",
        color="hazard_class", hover_name="workshop_id", hover_data=["area","review_flag"],
        title="Recent incidents vs equipment load",
        labels={"incident_count_90d":"Incidents in last 90 days","equipment_load_pct":"Equipment load (%)"},
    )
    fig.update_layout(height=500, margin=dict(l=10,r=10,t=55,b=10))
    st.plotly_chart(fig, use_container_width=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("### Load bands")
        bins = pd.cut(df["equipment_load_pct"], bins=[-1,60,80,100,120,999], labels=["≤60%","61–80%","81–100%","101–120%",">120%"]).value_counts().sort_index()
        st.plotly_chart(px.bar(bins.reset_index(name="workshops"), x="equipment_load_pct", y="workshops", text_auto=True), use_container_width=True)
    with c2:
        st.markdown("### Incident pressure")
        st.dataframe(df[["workshop_id","area","incident_count_90d","incident_risk","electrical_hazard_screening_score"]].sort_values("incident_count_90d", ascending=False).head(12), use_container_width=True, hide_index=True)

elif page == "Workshop Profiles":
    st.subheader("Workshop profiles")
    area = st.selectbox("Filter area", ["All"] + sorted(df["area"].dropna().astype(str).unique().tolist()))
    view = df if area == "All" else df[df["area"].astype(str) == area]
    st.dataframe(
        view[["workshop_id","area","hazard_class","electrical_hazard_screening_score","dominant_driver","equipment_load_pct","workshop_occupancy","inspection_date"]]
        .sort_values("electrical_hazard_screening_score", ascending=False),
        use_container_width=True, hide_index=True)

elif page == "Priority Queue":
    st.subheader("Priority inspection queue")
    threshold = st.slider("Minimum screening score", 0, 100, 55, 5)
    queue = df[df["electrical_hazard_screening_score"] >= threshold].sort_values("electrical_hazard_screening_score", ascending=False)
    st.metric("Records meeting threshold", len(queue))
    st.dataframe(queue[["workshop_id","area","electrical_hazard_screening_score","hazard_class","dominant_driver","review_flag"]], use_container_width=True, hide_index=True)

elif page == "Scenario Lab":
    st.subheader("Scenario lab")
    selected = st.selectbox("Baseline workshop", df["workshop_id"].astype(str).tolist())
    row = df[df["workshop_id"].astype(str) == selected].iloc[0]
    c1,c2,c3 = st.columns(3)
    with c1:
        load_change = st.slider("Change equipment load (%)", -30.0, 40.0, 0.0, 5.0)
        wiring_delta = st.slider("Wiring condition change", -30.0, 30.0, 0.0, 5.0)
    with c2:
        grounding_delta = st.slider("Grounding condition change", -30.0, 30.0, 0.0, 5.0)
        extension_delta = st.slider("Extension-cord condition change", -30.0, 30.0, 0.0, 5.0)
    with c3:
        moisture_delta = st.slider("Moisture exposure change", -40.0, 40.0, 0.0, 5.0)
        incident_delta = st.slider("Incident-count change", -3, 5, 0, 1)
    result = scenario_score(row, load_change_pct=load_change, wiring_delta=wiring_delta, grounding_delta=grounding_delta, moisture_delta=moisture_delta, extension_delta=extension_delta, incident_delta=incident_delta)
    base_score = float(row["electrical_hazard_screening_score"])
    r1,r2,r3,r4 = st.columns(4)
    with r1: metric_card("BASE SCORE", f"{base_score:.1f}", str(row["hazard_class"]))
    with r2: metric_card("SCENARIO SCORE", f"{result['score']:.1f}", str(result['class']))
    with r3: metric_card("CHANGE", f"{result['score']-base_score:+.1f}", "points")
    with r4: metric_card("DOMINANT DRIVER", result["driver"], "scenario")

    compare = pd.DataFrame({"state":["Baseline","Scenario"],"score":[base_score,result["score"]]})
    st.plotly_chart(px.bar(compare, x="state", y="score", color="state", text_auto=".1f", title="Before vs after screening score"), use_container_width=True)

elif page == "Image Review":
    st.subheader("Optional local inspection-image review")
    st.markdown('<div class="small-note">Upload a local inspection photo for generic visual-signal extraction. No image leaves the application. The result is a visual-anomaly signal, not a certified electrical hazard finding.</div>', unsafe_allow_html=True)
    img = st.file_uploader("Inspection image", type=["png","jpg","jpeg","webp"], key="inspection_image")
    if img:
        data = img.getvalue()
        result = analyze_inspection_image(data)
        left,right = st.columns([0.8,1.2])
        with left:
            st.image(data, caption=img.name, use_container_width=True)
        with right:
            metric_card("VISUAL SIGNAL", f"{result['visual_signal_score']}/100", "generic local visual signal")
            st.write(f"Brightness: {result['brightness']}%")
            st.write(f"Contrast: {result['contrast']}%")
            st.write(f"Edge density: {result['edge_density']}%")
            st.info(result["note"])
            st.download_button("Download image review JSON", data=pd.Series(result).to_json(indent=2), file_name="inspection_image_review.json", mime="application/json")
    else:
        st.info("No image uploaded. CSV-based scoring continues without image-derived input.")

elif page == "Reports & Export":
    st.subheader("Reports & export")
    report = df[["workshop_id","area","inspection_date","electrical_hazard_screening_score","hazard_class","dominant_driver","review_flag","equipment_load_pct","incident_count_90d"]].sort_values("electrical_hazard_screening_score", ascending=False)
    st.dataframe(report, use_container_width=True, hide_index=True)
    csv_bytes = report.to_csv(index=False).encode("utf-8")
    st.download_button("Download screening report (CSV)", data=csv_bytes, file_name="workshop_electrical_screening_report.csv", mime="text/csv")
    md = "# Workshop Electrical Hazard Screening Report\n\n"
    md += f"Records: {len(df)}\n\nAverage score: {m['avg_score']}\n\nHigh/Critical: {m['high_or_critical']}\n\n"
    md += "\n```\n" + report.to_string(index=False) + "\n```\n"
    st.download_button("Download report summary (Markdown)", data=md.encode("utf-8"), file_name="workshop_electrical_screening_report.md", mime="text/markdown")

else:
    st.subheader("Data explorer")
    st.caption(f"Required fields: {', '.join(REQUIRED_COLUMNS)}")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("### Data quality")
    quality = pd.DataFrame({"column": df.columns, "missing": df.isna().sum().values, "dtype": df.dtypes.astype(str).values})
    st.dataframe(quality, use_container_width=True, hide_index=True)
