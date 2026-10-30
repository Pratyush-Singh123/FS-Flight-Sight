"""
SkyFlow – Air Traffic Control & Airspace Management System (ATCMS)
Main System Overview & Architecture Dashboard
Course: Database Management Systems (DBMS)
"""

import streamlit as st
import pandas as pd
import db

st.set_page_config(
    page_title="SkyFlow ATCMS - Overview",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 8px;
        padding: 1rem;
        border-left: 5px solid #2563EB;
    }
    .member-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✈️ SkyFlow – Air Traffic Control & Airspace Management System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Indian Domestic Airspace & Airport Network Management Platform | Course: DBMS (3-Member Architecture)</div>', unsafe_allow_html=True)

# System Health & Engine Status
sys_status = db.get_database_status()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="DBMS Engine", value=sys_status["engine"].split(" ")[0], help="PostgreSQL or SQLite dual engine")
with col2:
    st.metric(label="Master Indian Hubs", value=sys_status["counts"].get("AIRPORT", 0), help="DEL, BOM, BLR, MAA, etc.")
with col3:
    st.metric(label="Registered Fleet", value=sys_status["counts"].get("AIRCRAFT", 0), help="DGCA VT- tail registrations")
with col4:
    st.metric(label="Scheduled Flight Legs", value=sys_status["counts"].get("FLIGHT", 0), help="Active operational flights")

st.markdown("---")

# Architecture & Member Work Breakdown
st.subheader("👥 3-Member Parallel Development Architecture")
st.markdown("""
SkyFlow ATCMS is architected to allow 3 team members to develop and demonstrate their respective relational modules 
independently while sharing a unified relational schema contract.
""")

col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    st.markdown("""
    <div class="member-card">
        <h4>🏢 Member 1: Ground Infrastructure</h4>
        <p><strong>Lead:</strong> Airport Ground & Hub Management</p>
        <p><strong>Tables Owned:</strong><br><code>AIRPORT</code>, <code>RUNWAY</code>, <code>GATE</code>, <code>GATE_ASSIGNMENT</code></p>
        <p><strong>Responsibilities:</strong> Runway surface states, terminal gate turnaround schedules, zero-overlap reservation constraints.</p>
        <p><em>Navigate via sidebar to Page 1</em></p>
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown("""
    <div class="member-card" style="border: 2px solid #2563EB; background-color: #EFF6FF;">
        <h4>✈️ Member 2: Flight Operations (ACTIVE)</h4>
        <p><strong>Lead:</strong> Commercial Fleet & Scheduling</p>
        <p><strong>Tables Owned:</strong><br><code>AIRLINE</code>, <code>AIRCRAFT</code>, <code>FLIGHT</code></p>
        <p><strong>Responsibilities:</strong> Fleet registry, domestic scheduling, state machine transitions, On-Time Performance (OTP) analytics, route density.</p>
        <p><strong>👉 Click "2 Flight Operations" in the left sidebar to access!</strong></p>
    </div>
    """, unsafe_allow_html=True)

with col_m3:
    st.markdown("""
    <div class="member-card">
        <h4>📡 Member 3: ATC Tower & Clearances</h4>
        <p><strong>Lead:</strong> Airspace & Safety Compliance</p>
        <p><strong>Tables Owned:</strong><br><code>AIRSPACE_SECTOR</code>, <code>CONTROLLER</code>, <code>FLIGHT_CLEARANCE</code>, <code>INCIDENT_LOG</code></p>
        <p><strong>Responsibilities:</strong> Sector vertical boundaries, clearance ledger, safety violation triggers, controller shift tracking.</p>
        <p><em>Navigate via sidebar to Page 3</em></p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Quick Navigation & Database State
st.subheader("📊 Live Relational Database Catalog")
c_tbl1, c_tbl2 = st.columns([1, 2])

with c_tbl1:
    counts_df = pd.DataFrame([
        {"Entity": tbl, "Table Count": count}
        for tbl, count in sys_status["counts"].items()
    ])
    st.dataframe(counts_df, use_container_width=True, hide_index=True)

with c_tbl2:
    st.markdown("#### 🎯 Quick Member 2 Demonstration Highlights")
    st.markdown("""
    - **Interactive Flight Dispatch Board:** Multi-criteria filtering by flight number, status, carrier, and airport.
    - **Database Constraint Verification:** Built-in checks for `origin <> dest` and `arrival > departure`.
    - **Flight Lifecycle State Machine:** Seamless transition (`SCHEDULED` ➔ `BOARDING` ➔ `TAXIING` ➔ `AIRBORNE` ➔ `LANDED`).
    - **Course SQL Query Demonstrations:** Live execution of On-Time Performance (OTP) queries, High-Density Corridors (`GROUP BY / HAVING`), and Correlated Subqueries.
    """)
    st.info("💡 To evaluate Member 2's portal, select **2_Flight_Operations** from the sidebar.")
