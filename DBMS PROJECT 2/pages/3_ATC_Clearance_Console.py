"""
SkyFlow ATCMS - ATC Clearance Console & Safety Dashboard (Page 3)
Owned by: Member 3 (Air Traffic Control Tower, En-Route & Safety Lead)
Course: Database Management Systems (DBMS)

Tables Managed: AIRSPACE_SECTOR, CONTROLLER, FLIGHT_CLEARANCE, INCIDENT_LOG
"""

import streamlit as st
import pandas as pd
import db

st.set_page_config(page_title="ATC Clearance Console - Member 3", page_icon="📡", layout="wide")

st.title("📡 ATC Tower Clearance Console & Safety Dashboard")
st.caption("SkyFlow ATCMS Subsystem | **Member 3 Scope:** Airspace Sectors, En-Route Clearances & Safety Incident Audit")

st.info("💡 **Team Parallel Architecture Note:** This module is owned and maintained by **Member 3**. Member 2 manages **2_Flight_Operations**.")

# Active Airborne Targets Feeds
st.subheader("🎯 Active Airborne Flight Vectors")
airborne = db.get_flights(status="AIRBORNE")
if airborne:
    st.dataframe(pd.DataFrame([
        {
            "Flight #": a["flight_number"],
            "Airline": a["airline_name"],
            "Tail Reg": a["aircraft_reg_no"],
            "Model": a["aircraft_model"],
            "Route": f"{a['origin_airport']} ➔ {a['dest_airport']}",
            "Actual Dep": a["actual_departure"],
            "Status": a["current_status"]
        } for a in airborne
    ]), use_container_width=True, hide_index=True)
else:
    st.info("No active airborne targets in radar sector.")

# Controllers on Duty & Sectors
st.subheader("👨‍✈️ ATC Duty Roster & FIR Sectors")
conn = db.get_connection()
cursor = conn.cursor()
try:
    cursor.execute("SELECT sector_id, sector_name, floor_altitude_ft, ceiling_altitude_ft, max_capacity FROM AIRSPACE_SECTOR")
    sectors = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT controller_id, first_name || ' ' || last_name AS name, license_number, certification_level, shift_start, shift_end FROM CONTROLLER")
    controllers = [dict(row) for row in cursor.fetchall()]
finally:
    cursor.close()
    conn.close()

c1, c2 = st.columns(2)
with c1:
    st.markdown("#### Airspace Sectors (FIRs)")
    st.dataframe(pd.DataFrame(sectors), use_container_width=True, hide_index=True)
with c2:
    st.markdown("#### Controllers on Duty")
    st.dataframe(pd.DataFrame(controllers), use_container_width=True, hide_index=True)
