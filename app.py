import streamlit as st
import db

st.set_page_config(
    page_title="SkyFlow ATCMS | Air Traffic Control Management System",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database tables and triggers
db.init_database()

st.title("✈️ SkyFlow – Air Traffic Control & Airspace Management System")
st.markdown("### High-Density Indian Airspace & Airport Network DBMS Platform")
st.caption("Course: Database Management Systems (DBMS) | Parallel 3-Member Architecture")

st.divider()

# Connection Diagnostics
conn, engine = db.get_connection()
conn.close()

st.success(f" Connected to Database Engine: **{engine.upper()}** (Transactional Integrity & Safety Triggers Active)")

col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.subheader("🏢 Member 1: Ground & Hubs")
    st.markdown("""
    - **Scope:** Multi-airport ground assets, runways, and terminal gates.
    - **Entities:** `AIRPORT`, `RUNWAY`, `GATE`, `GATE_ASSIGNMENT`
    - **Key Feature:** Gate turnaround management and runway length verifications.
    """)
    st.info("Navigate via sidebar to `1_Airport_Ground_Control`")

with col_info2:
    st.subheader("🛫 Member 2: Flight Operations")
    st.markdown("""
    - **Scope:** Commercial fleet scheduling and turnaround dispatch.
    - **Entities:** `AIRLINE`, `AIRCRAFT`, `FLIGHT`
    - **Key Feature:** Flight status tracking (`SCHEDULED` ➔ `AIRBORNE` ➔ `LANDED`).
    """)
    st.info("Navigate via sidebar to `2_Flight_Operations`")

with col_info3:
    st.subheader("📡 Member 3: ATC & Safety (Active)")
    st.markdown("""
    - **Scope:** 3D FIR airspace, tower controllers, real-time clearances, and safety incident logs.
    - **Entities:** `AIRSPACE_SECTOR`, `CONTROLLER`, `FLIGHT_CLEARANCE`, `INCIDENT_LOG`
    - **Key Feature:** Automated Runway Safety Interlock Triggers & Audit Ledger.
    """)
    st.success("👉 Go directly to `3_ATC_Clearance_Console` in sidebar!")

st.divider()

st.markdown("### 🗺️ System Architecture & Schema Overview")
st.markdown("""
The SkyFlow relational database operates on a frozen, normalized contract (3NF/BCNF) ensuring that all 3 members interact safely without conflicting schemas:
- **Zero-Overlap Runway Occupancy:** Member 3's clearance triggers inspect Member 1's runway status in real time before granting takeoff or landing clearances.
- **Flight Trajectory Integrity:** Member 3's clearances directly update and audit the status of Member 2's scheduled flights.
""")
