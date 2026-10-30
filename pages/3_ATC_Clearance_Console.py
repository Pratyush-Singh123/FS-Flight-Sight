import streamlit as st
import pandas as pd
from datetime import datetime
import db

# Page Configuration
st.set_page_config(
    page_title="ATC Clearance Console | SkyFlow",
    page_icon="📡",
    layout="wide"
)

# Initialize DB
db.init_database()

# Custom Styling
st.markdown("""
<style>
    .atc-header {
        background: linear-gradient(135deg, #064e3b 0%, #047857 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .atc-title { font-size: 1.8rem; font-weight: 700; margin: 0; color: #ffffff; }
    .atc-subtitle { font-size: 0.95rem; color: #a7f3d0; margin-top: 0.25rem; }
</style>
""", unsafe_allow_html=True)

# Header & Branding
st.markdown("""
<div class="atc-header">
    <div class="atc-title">📡 Tower Radar & En-Route ATC Clearance Console</div>
    <div class="atc-subtitle">SkyFlow IOCC Module 3 (Member 3 Lead) • Airspace Management, Real-Time Clearances & Safety Incident Black-Box Ledger</div>
</div>
""", unsafe_allow_html=True)

# Top Level KPI Metrics Bar
flights_df = db.get_active_flights()
controllers_df = db.get_controllers()
clearances_df = db.get_recent_clearances(50)
incidents_df = db.get_incident_logs()

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    airborne_count = len(flights_df[flights_df['current_status'] == 'AIRBORNE'])
    st.metric("✈️ Active Flights Airborne", airborne_count, delta=f"{len(flights_df)} tracked")
with col_m2:
    st.metric("👮 Controllers on Shift", len(controllers_df))
with col_m3:
    st.metric("📜 Clearances Issued", len(clearances_df))
with col_m4:
    critical_incidents = len(incidents_df[incidents_df['severity'].isin(['HIGH', 'CRITICAL'])]) if not incidents_df.empty else 0
    st.metric("🚨 Critical Anomaly Logs", critical_incidents, delta=f"{len(incidents_df)} total incidents", delta_color="inverse")

st.divider()

# Main Navigation Tabs
tab_clearance, tab_ledger, tab_incidents, tab_analytics, tab_demo = st.tabs([
    "🛫 1. Issue ATC Clearance", 
    "📜 2. Black-Box Audit Ledger", 
    "🚨 3. Safety & Incident Filing", 
    "📊 4. Workload & Sector Analytics",
    "🎯 5. Examiner Live Demo Mode"
])

# -----------------------------------------------------------------------------
# TAB 1: ISSUE ATC CLEARANCE
# -----------------------------------------------------------------------------
with tab_clearance:
    st.subheader("Transmit Air Traffic Control Clearance")
    st.markdown("""
    Issue formal, timestamped clearance instructions to aircraft operating in local tower airspace or en-route FIR sectors.  
    **Database Integrity:** All `TAKEOFF` and `LANDING` clearances enforce automated **Runway Safety Triggers** to prevent runway incursions.
    """)

    col_form, col_context = st.columns([1.8, 1.2])

    with col_form:
        with st.form("issue_clearance_form", clear_on_submit=False):
            st.markdown("#### Clearance Parameters")

            # Flight Selector
            if flights_df.empty:
                st.warning("No active flights currently available to receive clearances.")
                flight_options = {}
            else:
                flight_options = {
                    f"{row['flight_number']} ({row['airline_name']} | {row['origin_airport']} ➔ {row['dest_airport']} | Status: {row['current_status']})": row['flight_id']
                    for _, row in flights_df.iterrows()
                }
            selected_flight_label = st.selectbox("Select Target Flight", options=list(flight_options.keys()) if flight_options else ["None"])

            # Controller Selector
            controller_options = {
                f"{row['full_name']} [{row['certification_level']}] – Lic: {row['license_number']}": row['controller_id']
                for _, row in controllers_df.iterrows()
            }
            selected_controller_label = st.selectbox("Authorizing Controller", options=list(controller_options.keys()))

            # Clearance Type
            clearance_types = ['PUSHBACK', 'TAXI', 'TAKEOFF', 'ALTITUDE_CHANGE', 'HEADING', 'LANDING']
            selected_clearance_type = st.selectbox("Clearance Instruction Type", clearance_types)

            # Conditional Fields
            runway_id = None
            altitude = None
            heading = None

            if selected_clearance_type in ['TAKEOFF', 'LANDING']:
                st.markdown("##### 🛫 Runway Allocation (Safety Interlocked)")
                runways_df = db.get_runways()
                runway_options = {
                    f"{row['airport_code']} Runway {row['runway_designator']} ({row['length_meters']}m) – Live Status: {row['current_status']}": (row['runway_id'], row['current_status'])
                    for _, row in runways_df.iterrows()
                }
                selected_runway_label = st.selectbox("Designated Runway", options=list(runway_options.keys()))
                if selected_runway_label:
                    runway_id, r_stat = runway_options[selected_runway_label]
                    if r_stat != 'AVAILABLE':
                        st.error(f"⚠️ Selected runway is currently **{r_stat}**! The database trigger will reject this clearance.")
                    else:
                        st.success("✅ Runway is AVAILABLE. Trigger will grant clearance and reserve the runway.")

            if selected_clearance_type in ['TAKEOFF', 'ALTITUDE_CHANGE']:
                altitude = st.slider("Assigned Flight Level / Altitude (ft)", min_value=1000, max_value=46000, value=36000, step=1000)

            if selected_clearance_type in ['TAKEOFF', 'HEADING']:
                heading = st.number_input("Assigned Magnetic Heading (°)", min_value=0, max_value=360, value=90, step=5)

            submitted = st.form_submit_button("📡 TRANSMIT CLEARANCE TO AIRCRAFT", type="primary", use_container_width=True)

            if submitted:
                if not flight_options:
                    st.error("No valid flight selected.")
                else:
                    flight_id = flight_options[selected_flight_label]
                    controller_id = controller_options[selected_controller_label]
                    success, msg = db.issue_clearance(
                        flight_id=flight_id,
                        controller_id=controller_id,
                        clearance_type=selected_clearance_type,
                        runway_id=runway_id,
                        altitude=altitude,
                        heading=heading
                    )
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(msg)

    with col_context:
        st.markdown("#### Live Surface Status")
        st.caption("Active Runway States across Indian Hubs")
        runways_live = db.get_runways()
        for _, r in runways_live.iterrows():
            badge_color = "🟢" if r['current_status'] == 'AVAILABLE' else ("🔴" if r['current_status'] == 'OCCUPIED' else "🟡")
            st.markdown(f"**{r['airport_code']}** `Rwy {r['runway_designator']}`: {badge_color} **{r['current_status']}** ({r['length_meters']}m)")

        st.markdown("---")
        st.markdown("#### Quick Runway Override for Testing")
        st.caption("Toggle runway availability to demonstrate trigger collision behavior:")
        override_runway = st.selectbox("Select Runway to Toggle", options=runways_live['runway_id'].tolist(), 
                                       format_func=lambda x: f"Runway ID {x} ({runways_live.loc[runways_live['runway_id']==x, 'airport_code'].values[0]} {runways_live.loc[runways_live['runway_id']==x, 'runway_designator'].values[0]})")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Mark OCCUPIED", use_container_width=True):
                db.set_runway_status(override_runway, "OCCUPIED")
                st.toast("Runway set to OCCUPIED", icon="🔴")
                st.rerun()
        with col_btn2:
            if st.button("Mark AVAILABLE", use_container_width=True):
                db.set_runway_status(override_runway, "AVAILABLE")
                st.toast("Runway cleared to AVAILABLE", icon="🟢")
                st.rerun()

# -----------------------------------------------------------------------------
# TAB 2: BLACK-BOX AUDIT LEDGER
# -----------------------------------------------------------------------------
with tab_ledger:
    st.subheader("Black-Box ATC Clearance Audit Ledger")
    st.markdown("Immutable record of all digital and voice clearances issued to flights. Preserved for incident investigations and DGCA safety audits.")

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search_kw = st.text_input("🔍 Search by Flight Number or Controller Name", "")
    with col_f2:
        type_filter = st.selectbox("Filter Instruction", ["ALL"] + ['PUSHBACK', 'TAXI', 'TAKEOFF', 'ALTITUDE_CHANGE', 'HEADING', 'LANDING'])

    df_clearances = db.get_recent_clearances(50)
    if not df_clearances.empty:
        if search_kw:
            df_clearances = df_clearances[
                df_clearances['flight_number'].str.contains(search_kw, case=False, na=False) |
                df_clearances['controller'].str.contains(search_kw, case=False, na=False)
            ]
        if type_filter != "ALL":
            df_clearances = df_clearances[df_clearances['clearance_type'] == type_filter]

        st.dataframe(
            df_clearances,
            column_config={
                "clearance_id": "Clearance ID",
                "issued_timestamp": "Timestamp (UTC/IST)",
                "flight_number": "Flight #",
                "callsign_prefix": "Callsign",
                "clearance_type": "Instruction",
                "runway": "Assigned Runway",
                "assigned_altitude_ft": st.column_config.NumberColumn("Altitude (ft)", format="%d ft"),
                "assigned_heading_deg": st.column_config.NumberColumn("Heading", format="%d°"),
                "controller": "Authorizing Officer",
                "certification_level": "Certification"
            },
            hide_index=True,
            use_container_width=True
        )

        csv = df_clearances.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Clearance Audit Ledger (CSV)",
            data=csv,
            file_name=f"skyflow_clearance_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No clearances found.")

# -----------------------------------------------------------------------------
# TAB 3: SAFETY & INCIDENT FILING
# -----------------------------------------------------------------------------
with tab_incidents:
    st.subheader("Flight Safety Incident & Anomaly Filing Portal")
    st.markdown("Record, investigate, and audit flight safety occurrences, near-misses, runway incursions, and weather diversions.")

    col_inc_form, col_inc_list = st.columns([1.5, 1.5])

    with col_inc_form:
        st.markdown("#### 📝 File Safety Occurrence Report")
        with st.form("incident_filing_form", clear_on_submit=True):
            all_flights_df = db.get_all_flights()
            all_flight_opts = {"Airport / Ground Perimeter (No specific flight)": None}
            for _, r in all_flights_df.iterrows():
                all_flight_opts[f"{r['flight_number']} ({r['airline_name']} | {r['origin_airport']} ➔ {r['dest_airport']})"] = r['flight_id']

            inc_flight_lbl = st.selectbox("Involved Flight", options=list(all_flight_opts.keys()))
            inc_flight_id = all_flight_opts[inc_flight_lbl]

            inc_controller_opts = {
                f"{r['full_name']} ({r['certification_level']})": r['controller_id']
                for _, r in controllers_df.iterrows()
            }
            inc_ctrl_lbl = st.selectbox("Reporting Officer", options=list(inc_controller_opts.keys()))
            inc_ctrl_id = inc_controller_opts[inc_ctrl_lbl]

            inc_type = st.selectbox("Incident Category", ['NEAR_MISS', 'RUNWAY_INCURSION', 'ALTITUDE_BUST', 'BIRD_STRIKE', 'WEATHER_DIVERT'])
            inc_severity = st.select_slider("Severity Level", options=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], value='MEDIUM')
            inc_desc = st.text_area("Occurrence Description / Investigation Notes", placeholder="Provide detailed ATC radar notes, altitude deviations, or surface coordinates...")

            inc_submit = st.form_submit_button("🚨 FILE OFFICIAL INCIDENT REPORT", type="primary", use_container_width=True)
            if inc_submit:
                if not inc_desc or len(inc_desc.strip()) < 10:
                    st.error("Please provide a meaningful narrative description (min 10 characters).")
                else:
                    success, msg = db.file_incident(inc_flight_id, inc_ctrl_id, inc_type, inc_severity, inc_desc)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with col_inc_list:
        st.markdown("#### 🚨 Historical Incident Audit Dossier")
        inc_logs = db.get_incident_logs()
        if not inc_logs.empty:
            for _, inc in inc_logs.iterrows():
                sev = inc['severity']
                card_border = "🔴" if sev == "CRITICAL" else ("🟠" if sev == "HIGH" else ("🟡" if sev == "MEDIUM" else "🔵"))
                with st.expander(f"{card_border} #{inc['incident_id']} | {inc['incident_type']} | Severity: {sev} ({inc['incident_time']})", expanded=(sev in ['HIGH', 'CRITICAL'])):
                    st.markdown(f"**Flight:** `{inc['flight_number']}`")
                    st.markdown(f"**Reported By:** {inc['reported_by_controller']} (*{inc['certification_level']}*)")
                    st.markdown(f"**Notes:** {inc['description']}")
        else:
            st.info("Zero safety incidents on record.")

# -----------------------------------------------------------------------------
# TAB 4: WORKLOAD & SECTOR ANALYTICS
# -----------------------------------------------------------------------------
with tab_analytics:
    st.subheader("ATC Operations, Controller Workload & Airspace Analytics")
    st.markdown("Analytical insights computed via aggregate relational queries (`GROUP BY`, `HAVING`, and subqueries).")

    col_a1, col_a2 = st.columns(2)

    with col_a1:
        st.markdown("#### 👮 Controller Workload Metrics (Query 2)")
        st.caption("Clearance throughput and distinct aircraft managed per officer:")
        workload_df = db.get_controller_workload()
        if not workload_df.empty:
            st.dataframe(
                workload_df[['controller_name', 'certification_level', 'sector_name', 'total_clearances_issued', 'distinct_aircraft_handled']],
                column_config={
                    "controller_name": "Controller",
                    "certification_level": "Certification",
                    "sector_name": "Sector",
                    "total_clearances_issued": st.column_config.ProgressColumn("Clearances Issued", min_value=0, max_value=20, format="%d"),
                    "distinct_aircraft_handled": "Aircraft Handled"
                },
                hide_index=True,
                use_container_width=True
            )
            # Altair / Streamlit Bar Chart
            st.bar_chart(workload_df.set_index('controller_name')['total_clearances_issued'])
        else:
            st.info("No controller activity recorded yet.")

    with col_a2:
        st.markdown("#### 🌐 Indian Airspace FIR Sectors (Query 4)")
        st.caption("Altitude boundaries and capacity limits:")
        sector_df = db.get_sector_utilization()
        if not sector_df.empty:
            st.dataframe(
                sector_df[['sector_name', 'floor_altitude_ft', 'ceiling_altitude_ft', 'max_capacity', 'active_controllers_assigned']],
                column_config={
                    "sector_name": "Airspace Sector / FIR",
                    "floor_altitude_ft": st.column_config.NumberColumn("Floor (ft)", format="%d ft"),
                    "ceiling_altitude_ft": st.column_config.NumberColumn("Ceiling (ft)", format="%d ft"),
                    "max_capacity": "Max Aircraft Capacity",
                    "active_controllers_assigned": "Controllers Assigned"
                },
                hide_index=True,
                use_container_width=True
            )

    st.markdown("---")
    st.markdown("#### 🛰️ Live Airborne Flights Radar View (Query 1)")
    st.caption("Active flights joined with carrier, route, authorizing controller, and the latest clearance subquery:")
    radar_df = db.get_airborne_radar_flights()
    if not radar_df.empty:
        st.dataframe(
            radar_df[['flight_number', 'airline_name', 'aircraft_model', 'route', 'latest_instruction', 'assigned_altitude_ft', 'assigned_heading_deg', 'authorizing_controller']],
            column_config={
                "flight_number": "Flight #",
                "airline_name": "Carrier",
                "aircraft_model": "Aircraft",
                "route": "Route",
                "latest_instruction": "Latest Command",
                "assigned_altitude_ft": st.column_config.NumberColumn("Altitude", format="%d ft"),
                "assigned_heading_deg": st.column_config.NumberColumn("Heading", format="%d°"),
                "authorizing_controller": "Authorizing Officer"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No flights currently in AIRBORNE status.")

# -----------------------------------------------------------------------------
# TAB 5: EXAMINER LIVE DEMO MODE
# -----------------------------------------------------------------------------
with tab_demo:
    st.subheader("🎯 Step-by-Step Examiner Evaluation Demonstration")
    st.markdown("""
    Use this guided walk-through during project evaluation to verify all requirements specified in **Section 14 of the Project Instructions** and **Section 12.3 of the Technical Blueprint**.
    """)

    st.markdown("""
    ### 1. Verification of Member 3 Relational Tables
    - **`AIRSPACE_SECTOR`**: 3D spatial sectors with checked altitude ceilings.
    - **`CONTROLLER`**: DGCA licensed ATC controllers with shift times and certification constraints.
    - **`FLIGHT_CLEARANCE`**: Append-only black-box clearance instructions.
    - **`INCIDENT_LOG`**: Safety anomaly records with priority grading.
    """)

    st.markdown("### 2. Live Safety Trigger Test: Runway Collision Prevention")
    st.info("""
    **Evaluation Test:**
    1. Select a runway that is currently **`OCCUPIED`** (e.g. Runway 1 at DEL).
    2. Attempt to issue a **`TAKEOFF`** or **`LANDING`** clearance on that runway.
    3. Notice how the database trigger immediately aborts the transaction with:
       `⚠️ SAFETY INTERLOCK TRIGGERED: Runway is currently OCCUPIED or CLOSED!`
    4. Next, toggle the runway to **`AVAILABLE`** and issue the clearance.
    5. The trigger succeeds and automatically flips the runway state to **`OCCUPIED`**!
    """)

    st.markdown("### 3. Verification of Course SQL Syllabus Concepts")
    with st.expander("Show SQL Query 1: Multi-Table Join with Correlated Subquery"):
        st.code("""
SELECT 
    f.flight_number, al.airline_name, ac.model,
    f.origin_airport || ' -> ' || f.dest_airport AS route,
    fc.assigned_altitude_ft, fc.assigned_heading_deg,
    c.first_name || ' ' || c.last_name AS authorizing_controller
FROM FLIGHT f
JOIN AIRLINE al ON f.airline_id = al.airline_id
JOIN AIRCRAFT ac ON f.aircraft_reg_no = ac.aircraft_reg_no
JOIN FLIGHT_CLEARANCE fc ON f.flight_id = fc.flight_id
JOIN CONTROLLER c ON fc.controller_id = c.controller_id
WHERE f.current_status = 'AIRBORNE'
  AND fc.clearance_id = (
      SELECT MAX(sub_fc.clearance_id)
      FROM FLIGHT_CLEARANCE sub_fc
      WHERE sub_fc.flight_id = f.flight_id
  );
        """, language="sql")

    with st.expander("Show SQL Query 2: Aggregate Analysis with GROUP BY and HAVING"):
        st.code("""
SELECT 
    c.controller_id,
    c.first_name || ' ' || c.last_name AS controller_name,
    c.certification_level,
    COALESCE(sec.sector_name, 'Surface / Ground') AS sector_name,
    COUNT(fc.clearance_id) AS total_clearances_issued,
    COUNT(DISTINCT fc.flight_id) AS distinct_aircraft_handled
FROM CONTROLLER c
LEFT JOIN FLIGHT_CLEARANCE fc ON c.controller_id = fc.controller_id
LEFT JOIN AIRSPACE_SECTOR sec ON c.assigned_sector_id = sec.sector_id
GROUP BY c.controller_id, c.first_name, c.last_name, c.certification_level, sec.sector_name
HAVING COUNT(fc.clearance_id) > 0
ORDER BY total_clearances_issued DESC;
        """, language="sql")

    with st.expander("Show SQL Trigger DDL (PL/pgSQL & SQLite equivalent)"):
        st.code("""
CREATE OR REPLACE FUNCTION trg_fn_enforce_runway_safety()
RETURNS TRIGGER AS $$
DECLARE
    r_status VARCHAR(20);
BEGIN
    IF NEW.runway_id IS NOT NULL AND NEW.clearance_type IN ('TAKEOFF', 'LANDING') THEN
        SELECT current_status INTO r_status 
        FROM RUNWAY 
        WHERE runway_id = NEW.runway_id;

        IF r_status <> 'AVAILABLE' THEN
            RAISE EXCEPTION 'Runway Safety Violation: Runway ID % is currently %!', NEW.runway_id, r_status;
        END IF;

        UPDATE RUNWAY 
        SET current_status = 'OCCUPIED' 
        WHERE runway_id = NEW.runway_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
        """, language="sql")
