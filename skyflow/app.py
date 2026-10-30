import streamlit as st

st.set_page_config(
    page_title="SkyFlow - Air Traffic Control & Airport Network",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ SkyFlow: Air Traffic & Airport Management System")
st.markdown("### DBMS Mid-Semester Project | 3-Member Vertical Slice Architecture")

st.markdown("""
Welcome to **SkyFlow**, an integrated relational database application modeling Indian Air Traffic Control,
airport ground infrastructures, fleet management, and airspace sectors.

---
### 👥 Team Ownership & Modules
1. **Member 1 (Active Page): Ground Infrastructure & Terminal Movement**
   - Tables: `AIRPORT`, `RUNWAY`, `GATE`, `GATE_ASSIGNMENT`
   - Page: Navigate to **1_Airport_Ground_Control** in the left sidebar to manage runways, gates, and assignments.
2. **Member 2: Fleet Management & Flight Operations**
   - Tables: `AIRLINE`, `AIRCRAFT`, `FLIGHT`
3. **Member 3: Airspace & Incident Monitoring**
   - Tables: `AIRSPACE_SECTOR`, `CONTROLLER`, `FLIGHT_CLEARANCE`, `INCIDENT_LOG`

---
### 🛠️ Technology Stack
- **Database:** PostgreSQL (`skyflow_db`)
- **Driver:** `psycopg2`
- **Application Interface:** Streamlit (Python)
""")

st.info("👈 Use the left sidebar to navigate to **Airport Ground Control** to monitor ground status and manage gate assignments.")
