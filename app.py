"""
SkyFlow ATCMS - Integrated Operations Control Center (IOCC)
Master System Overview, Collaborative Architecture & Indian Airspace Network Platform
Course: Database Management Systems (DBMS) | 3-Member Unified Team Platform
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import db

st.set_page_config(
    page_title="SkyFlow IOCC | Air Traffic Control & Airspace Management System",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database tables and triggers
db.init_database()

# Humane Global Styling
st.markdown("""
<style>
    .iocc-header {
        background: linear-gradient(135deg, #091e3a 0%, #173866 50%, #1e4976 100%);
        padding: 2rem 2.5rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .iocc-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
        color: #ffffff;
    }
    .iocc-subtitle {
        font-size: 1.05rem;
        color: #93c5fd;
        margin-top: 0.4rem;
        font-weight: 400;
    }
    .iocc-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        margin-top: 0.8rem;
        color: #f8fafc;
    }
    .persona-card {
        border-radius: 12px;
        padding: 1.5rem;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, box-shadow 0.2s;
        height: 100%;
    }
    .persona-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .card-m1 { border-top: 5px solid #0284c7; }
    .card-m2 { border-top: 5px solid #2563eb; }
    .card-m3 { border-top: 5px solid #059669; }
    .lifecycle-container {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    .badge-live {
        display: inline-block;
        background: #dcfce7;
        color: #166534;
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# Humane IOCC Header
sys_status = db.get_database_status()
now_str = datetime.now().strftime("%d %b %Y • %H:%M:%S IST")

st.markdown(f"""
<div class="iocc-header">
    <div class="iocc-title">✈️ SkyFlow – Integrated Operations Control Center (IOCC)</div>
    <div class="iocc-subtitle">Collaborative Air Traffic Management, Ground Turnaround & Commercial Fleet System across Indian Airspace</div>
    <div class="iocc-badge">🛰️ Live Network Telemetry • {now_str} • Engine: {sys_status['engine']}</div>
</div>
""", unsafe_allow_html=True)

# Live Network High-Level Telemetry
col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)
with col_t1:
    st.metric("🏢 Aerodrome Hubs", sys_status["counts"].get("AIRPORT", 0), help="Delhi, Mumbai, Bengaluru, Chennai, Kolkata, Hyderabad, etc.")
with col_t2:
    st.metric("🛫 Active Flight Legs", sys_status["counts"].get("FLIGHT", 0), help="Scheduled and active operations today")
with col_t3:
    st.metric("✈️ Commercial Fleet", sys_status["counts"].get("AIRCRAFT", 0), help="DGCA VT- civil aircraft registered")
with col_t4:
    st.metric("👮 Licensed Controllers", sys_status["counts"].get("CONTROLLER", 0), help="Active Tower & Radar Approach officers")
with col_t5:
    st.metric("📜 ATC Clearances", sys_status["counts"].get("FLIGHT_CLEARANCE", 0), help="Timestamped immutable black-box ledger")

st.markdown("---")

# 3-Member Unified Work Breakdown Structure
st.subheader("👥 The 3 Collaborative Operational Wings")
st.markdown("Select a module in the sidebar or explore how each team member's domain connects into the unified schema:")

col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    st.markdown("""
    <div class="persona-card card-m1">
        <span class="badge-live">MODULE 1 • COMPLETED</span>
        <h3 style="margin-top: 0.5rem; color: #0369a1;">🏢 Ground & Terminal Hub</h3>
        <p><strong>Member 1 Lead:</strong> Ground Infrastructure & Terminal Movement</p>
        <p style="font-size: 0.9rem; color: #475569;">
            Manages aerodrome surface infrastructure across 12 Indian international hubs: physical runways, terminal bays, gate turnaround windows, and conflict prevention.
        </p>
        <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 0.8rem 0;">
        <p style="font-size: 0.85rem; margin: 0;"><strong>Tables:</strong> <code>AIRPORT</code>, <code>RUNWAY</code>, <code>GATE</code>, <code>GATE_ASSIGNMENT</code></p>
        <p style="font-size: 0.85rem; margin: 0.2rem 0;"><strong>Key Trigger:</strong> Gate Double-Booking Prevention Trigger</p>
        <p style="font-size: 0.85rem; color: #0284c7; font-weight: 600; margin-top: 0.5rem;">👉 Access via sidebar: 1_Airport_Ground_Control</p>
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown("""
    <div class="persona-card card-m2">
        <span class="badge-live">MODULE 2 • COMPLETED</span>
        <h3 style="margin-top: 0.5rem; color: #1d4ed8;">🛫 Fleet & Flight Operations</h3>
        <p><strong>Member 2 Lead:</strong> Commercial Fleet & Dispatch Operations</p>
        <p style="font-size: 0.9rem; color: #475569;">
            Coordinates domestic airline schedules, fleet profiles with DGCA VT- tail registrations, route density, flight lifecycle state transitions, and delay logging.
        </p>
        <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 0.8rem 0;">
        <p style="font-size: 0.85rem; margin: 0;"><strong>Tables:</strong> <code>AIRLINE</code>, <code>AIRCRAFT</code>, <code>FLIGHT</code></p>
        <p style="font-size: 0.85rem; margin: 0.2rem 0;"><strong>Key Feature:</strong> On-Time Performance (OTP) & Route Density Analytics</p>
        <p style="font-size: 0.85rem; color: #2563eb; font-weight: 600; margin-top: 0.5rem;">👉 Access via sidebar: 2_Flight_Operations</p>
    </div>
    """, unsafe_allow_html=True)

with col_m3:
    st.markdown("""
    <div class="persona-card card-m3">
        <span class="badge-live">MODULE 3 • COMPLETED</span>
        <h3 style="margin-top: 0.5rem; color: #047857;">📡 Tower & Airspace Safety</h3>
        <p><strong>Member 3 Lead:</strong> ATC Tower, En-Route Radar & Safety Audit</p>
        <p style="font-size: 0.9rem; color: #475569;">
            Supervises Indian FIR sectors (Delhi, Mumbai, Chennai, Kolkata), licensed controllers, real-time pushback/takeoff clearances, and safety incident reporting.
        </p>
        <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 0.8rem 0;">
        <p style="font-size: 0.85rem; margin: 0;"><strong>Tables:</strong> <code>AIRSPACE_SECTOR</code>, <code>CONTROLLER</code>, <code>FLIGHT_CLEARANCE</code>, <code>INCIDENT_LOG</code></p>
        <p style="font-size: 0.85rem; margin: 0.2rem 0;"><strong>Key Trigger:</strong> Runway Collision Prevention Safety Interlock</p>
        <p style="font-size: 0.85rem; color: #059669; font-weight: 600; margin-top: 0.5rem;">👉 Access via sidebar: 3_ATC_Clearance_Console</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Inter-Task Connectivity & End-to-End Flight Lifecycle
st.subheader("🔄 End-to-End Flight Lifecycle & Inter-Module Coordination")
st.markdown("""
The diagram below illustrates how a single commercial flight seamlessly passes through the responsibilities 
of Member 1, Member 2, and Member 3 at the database level:
""")

st.markdown("""
```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 SKYFLOW END-TO-END FLIGHT LIFECYCLE                                    │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
 1. GATE ALLOCATION (Member 1)                      ▼
    • Ground staff assigns Gate T3-01A to Flight 6E-204 in GATE_ASSIGNMENT.
    • Automated Trigger `trg_prevent_gate_double_booking` verifies zero time-overlap.
                                                    │
 2. FLIGHT DISPATCH (Member 2)                      ▼
    • Airline Dispatcher schedules Flight 6E-204 (DEL -> MAA) on A320neo (VT-ISN).
    • State moves from `SCHEDULED` ➔ `BOARDING` as turnaround progresses.
                                                    │
 3. TOWER PUSHBACK & TAXI (Member 3)                ▼
    • Controller logs PUSHBACK & TAXI instructions in FLIGHT_CLEARANCE.
    • Flight transitions to `TAXIING`.
                                                    │
 4. TAKEOFF SAFETY INTERLOCK (Member 3 ➔ Member 1)  ▼
    • Controller attempts TAKEOFF clearance on Runway 09/27 (DEL).
    • Automated Trigger `trg_runway_clearance_safety_abort` inspects Member 1's RUNWAY status:
      - If OCCUPIED/CLOSED: Transaction ABORTED with Safety Violation error!
      - If AVAILABLE: Clearance approved, RUNWAY auto-marked OCCUPIED, FLIGHT auto-moves to `AIRBORNE`.
                                                    │
 5. EN-ROUTE RADAR SECTOR (Member 3)                ▼
    • Cruising through Delhi & Mumbai FIR sectors with ALTITUDE and HEADING clearances.
    • Sector traffic limits enforced against `AIRSPACE_SECTOR.max_capacity`.
    • Any near-miss or turbulence anomaly filed into `INCIDENT_LOG`.
                                                    │
 6. APPROACH & LANDING (Member 3 ➔ Member 1 & 2)    ▼
    • Landing clearance granted on Runway 07/25 (MAA).
    • Trigger automatically transitions FLIGHT to `LANDED`, sets actual arrival time, and logs landing.
                                                    │
 7. TURNAROUND COMPLETION (Member 1)                ▼
    • Aircraft docks at Chennai Gate T1-04; previous departure turnaround marked `COMPLETED`.
```
""")

st.markdown("---")

# Live Network Radar Board
st.subheader("🌐 Live Indian Domestic Flight Radar Board")
st.caption("Real-time view joined across FLIGHT (M2), RUNWAY (M1), GATE (M1), and FLIGHT_CLEARANCE (M3)")

flights_live = db.get_flights()
if flights_live:
    df_live = pd.DataFrame(flights_live)
    st.dataframe(
        df_live[[
            'flight_number', 'airline_name', 'aircraft_reg_no', 'aircraft_model',
            'origin_airport', 'dest_airport', 'scheduled_departure', 'scheduled_arrival',
            'current_status', 'departure_delay_minutes'
        ]],
        column_config={
            "flight_number": "Flight #",
            "airline_name": "Carrier",
            "aircraft_reg_no": "Tail Reg",
            "aircraft_model": "Aircraft Type",
            "origin_airport": "Origin",
            "dest_airport": "Destination",
            "scheduled_departure": "Sched Dep",
            "scheduled_arrival": "Sched Arr",
            "current_status": "Status",
            "departure_delay_minutes": st.column_config.NumberColumn("Delay (mins)", format="%d min")
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("No flights currently on record.")
