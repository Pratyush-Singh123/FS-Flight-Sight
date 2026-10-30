import streamlit as st
import db

st.set_page_config(page_title="Airport Ground Control | SkyFlow", page_icon="🏢", layout="wide")

st.title("🏢 Airport Ground Control & Terminal Hub (Member 1)")
st.info("📌 **Owner:** Member 1 (Ground Infrastructure & Terminal Movement Lead)")

st.markdown("""
### Operational Scope
- Physical aerodromes, runways, terminal gates, and turnaround schedules.
- **Assigned Tables:** `AIRPORT`, `RUNWAY`, `GATE`, `GATE_ASSIGNMENT`
- **Current Integration:** Runway statuses (`AVAILABLE`, `OCCUPIED`, `CLOSED`) are read in real time by Member 3's ATC clearance triggers.
""")

st.divider()

# Live Runway & Hub Quick View
st.subheader("Current Hub Surface Status")
runways = db.get_runways()
st.dataframe(runways, hide_index=True, use_container_width=True)
