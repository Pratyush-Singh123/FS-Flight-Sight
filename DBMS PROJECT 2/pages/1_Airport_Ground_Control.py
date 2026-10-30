"""
SkyFlow ATCMS - Airport Ground & Terminal Movement (Page 1)
Owned by: Member 1 (Airport Ground & Hub Management Lead)
Course: Database Management Systems (DBMS)

Tables Managed: AIRPORT, RUNWAY, GATE, GATE_ASSIGNMENT
"""

import streamlit as st
import pandas as pd
import db

st.set_page_config(page_title="Airport Ground Control - Member 1", page_icon="🏢", layout="wide")

st.title("🏢 Airport Ground & Terminal Control")
st.caption("SkyFlow ATCMS Subsystem | **Member 1 Scope:** Aerodromes, Runways, Terminal Gates & Turnaround")

st.info("💡 **Team Parallel Architecture Note:** This module is owned and maintained by **Member 1**. Member 2 manages **2_Flight_Operations**.")

# Display Hub Status Summary
st.subheader("📍 Master Indian Aerodromes Managed by Member 1")
airports = db.get_airports()
st.dataframe(pd.DataFrame(airports), use_container_width=True, hide_index=True)

# Runway and Gate Summary
st.subheader("🛫 Runway & Gate Infrastructure")
conn = db.get_connection()
cursor = conn.cursor()
try:
    cursor.execute("""
        SELECT r.runway_id, r.airport_code, r.runway_designator, r.length_meters, r.current_status
        FROM RUNWAY r
        ORDER BY r.airport_code, r.runway_designator
    """)
    runways = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT g.gate_id, g.airport_code, g.terminal_number, g.gate_number, g.gate_category, g.current_status
        FROM GATE g
        ORDER BY g.airport_code, g.terminal_number, g.gate_number
    """)
    gates = [dict(row) for row in cursor.fetchall()]
finally:
    cursor.close()
    conn.close()

c1, c2 = st.columns(2)
with c1:
    st.markdown("#### Runways")
    st.dataframe(pd.DataFrame(runways), use_container_width=True, hide_index=True)
with c2:
    st.markdown("#### Terminal Gates")
    st.dataframe(pd.DataFrame(gates), use_container_width=True, hide_index=True)
