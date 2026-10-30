import streamlit as st
import pandas as pd
from datetime import datetime
import db

st.set_page_config(
    page_title="Airport Ground & Terminal Hub | SkyFlow",
    page_icon="🏢",
    layout="wide"
)

# Humane Custom Styling
st.markdown("""
<style>
    .hub-header {
        background: linear-gradient(135deg, #0f2b48 0%, #1e3a8a 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .hub-title { font-size: 1.8rem; font-weight: 700; margin: 0; color: #ffffff; }
    .hub-subtitle { font-size: 0.95rem; color: #93c5fd; margin-top: 0.25rem; }
    .rwy-card {
        border-radius: 10px;
        padding: 1rem;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        margin-bottom: 0.5rem;
    }
    .rwy-title { font-size: 1.1rem; font-weight: 700; margin: 0; color: #1e293b; }
    .rwy-meta { font-size: 0.85rem; color: #64748b; margin: 0.2rem 0; }
    .badge-available { color: #15803d; font-weight: 700; }
    .badge-occupied { color: #b91c1c; font-weight: 700; }
    .badge-closed { color: #b45309; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="hub-header">
    <div class="hub-title">🏢 Airport Ground Infrastructure & Terminal Movement</div>
    <div class="hub-subtitle">SkyFlow IOCC Module 1 (Member 1 Lead) • Aerodrome Surface, Runway Safety & Gate Turnaround Logistics</div>
</div>
""", unsafe_allow_html=True)

# Fetch all airports
airports_data = db.get_airports()
airport_dict = {f"{a['airport_code']} • {a['city']} ({a['airport_name']})": a['airport_code'] for a in airports_data}

col_sel1, col_sel2 = st.columns([2.5, 1.5])
with col_sel1:
    selected_label = st.selectbox("Select Airport Facility:", list(airport_dict.keys()), index=0)
    selected_code = airport_dict[selected_label]
with col_sel2:
    status_db = db.get_database_status()
    st.info(f"Connected: **{status_db['engine']}** | Active Hub: **{selected_code}**")

tabs = st.tabs([
    "📊 Ground Overview", 
    "🛬 Runways Management", 
    "🚪 Gates Status", 
    "📝 Gate Assignment & Overlap Guard", 
    "📈 Operational Reports & Analytics"
])

# ---------------------------------------------------------------------
# TAB 1: Ground Overview
# ---------------------------------------------------------------------
with tabs[0]:
    st.subheader(f"Ground Operations Status: {selected_code}")
    
    view_data = db.get_ground_dashboard_view(selected_code)
    if view_data:
        v = view_data[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Physical Runways", v['total_runways'], delta=f"{v['available_runways']} Available")
        c2.metric("Runway Occupancy", f"{v['occupied_runways']} Active", delta_color="inverse")
        c3.metric("Terminal Gates", v['total_gates'])
        c4.metric("Free Gates", v['free_gates'], delta=f"{v['total_gates'] - v['free_gates']} Occupied")
        st.caption(f"Aerodrome Elevation: **{v['elevation_ft']} ft MSL** | City Jurisdiction: **{v['city']}, India**")

    st.markdown("#### Active Gate Assignments & Turnaround Windows")
    q_active = """
        SELECT 
            ga.assignment_id,
            g.terminal_number AS terminal,
            g.gate_number,
            f.flight_number,
            f.origin_airport || ' ➔ ' || f.dest_airport AS route,
            ga.assigned_from,
            ga.assigned_until,
            ga.status
        FROM GATE_ASSIGNMENT ga
        JOIN GATE g ON ga.gate_id = g.gate_id
        JOIN FLIGHT f ON ga.flight_id = f.flight_id
        WHERE g.airport_code = ?
        ORDER BY ga.assigned_from ASC;
    """
    active_assignments = db.run_query(q_active, (selected_code,))
    if active_assignments:
        st.dataframe(pd.DataFrame(active_assignments), hide_index=True, use_container_width=True)
    else:
        st.info("No active gate assignments currently logged for this hub.")

# ---------------------------------------------------------------------
# TAB 2: Runway Management (Read + Update Status)
# ---------------------------------------------------------------------
with tabs[1]:
    st.subheader("Physical Runway Grid & Live State")
    st.markdown("""
    Monitor paved runways. **Safety Interlock:** If an ATC Controller attempts a takeoff or landing clearance 
    on an `OCCUPIED` or `CLOSED` runway, the database trigger automatically intercepts and blocks the command.
    """)
    
    runways_df = db.get_runways(selected_code)
    if not runways_df.empty:
        cols = st.columns(len(runways_df))
        for idx, (_, r) in enumerate(runways_df.iterrows()):
            stat = r['current_status']
            badge_class = "badge-available" if stat == "AVAILABLE" else ("badge-occupied" if stat == "OCCUPIED" else "badge-closed")
            emoji = "🟢" if stat == "AVAILABLE" else ("🔴" if stat == "OCCUPIED" else "🟡")
            with cols[idx]:
                st.markdown(
                    f"""
                    <div class="rwy-card">
                        <div class="rwy-title">Runway {r['runway_designator']}</div>
                        <div class="rwy-meta">{r['length_meters']}m paved • {r['surface_type']}</div>
                        <div class="{badge_class}">{emoji} {stat}</div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        
        st.divider()
        st.subheader("Update Surface Status (Ground Dispatcher)")
        with st.form("update_runway_form"):
            r_opts = {f"Runway {r['runway_designator']} (Current: {r['current_status']})": r['runway_id'] for _, r in runways_df.iterrows()}
            selected_r_label = st.selectbox("Select Target Runway:", options=list(r_opts.keys()))
            selected_r_id = r_opts[selected_r_label]
            new_status = st.selectbox("New Operational Status:", ["AVAILABLE", "OCCUPIED", "CLOSED"])
            submit_runway = st.form_submit_button("Update Runway Status", type="primary")
            
            if submit_runway:
                ok, msg = db.set_runway_status(selected_r_id, new_status)
                if ok:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"Failed to update status: {msg}")

# ---------------------------------------------------------------------
# TAB 3: Gate Status
# ---------------------------------------------------------------------
with tabs[2]:
    st.subheader("Terminal Parking Stands & Aerobridges")
    status_filter = st.radio("Filter By Operational State:", ["ALL", "AVAILABLE", "OCCUPIED", "MAINTENANCE"], horizontal=True)
    
    gates_data = db.get_gates(selected_code, status=status_filter)
    if gates_data:
        df_gates = pd.DataFrame(gates_data)
        st.dataframe(
            df_gates[['gate_id', 'terminal_number', 'gate_number', 'gate_category', 'gate_type', 'current_status']],
            column_config={
                "gate_id": "Gate ID",
                "terminal_number": "Terminal",
                "gate_number": "Bay #",
                "gate_category": "Flight Zone",
                "gate_type": "Bridge Type",
                "current_status": "Status"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No gates found matching the selected criteria.")

# ---------------------------------------------------------------------
# TAB 4: Assign Gate Form (Create / Add with Overlap Prevention Trigger)
# ---------------------------------------------------------------------
with tabs[3]:
    st.subheader("Terminal Gate Allocation & Conflict Interlock")
    st.markdown("""
    Schedule gate turnaround windows for passenger deplaning and ground handling.  
    **Database Integrity Rule:** The automated trigger `trg_prevent_gate_double_booking` rejects any attempt 
    to allocate a gate if its requested time interval overlaps with an existing reservation.
    """)
    
    local_gates = db.get_gates(selected_code)
    flights_data = db.get_flights()
    # Filter flights involving this airport
    hub_flights = [f for f in flights_data if f['origin_airport'] == selected_code or f['dest_airport'] == selected_code]
    
    col_assign, col_del = st.columns([1.5, 1.5])
    
    with col_assign:
        st.markdown("#### 📝 Book New Gate Assignment")
        if local_gates and hub_flights:
            with st.form("assign_gate_form"):
                flight_choice_map = {
                    f"{f['flight_number']} ({f['origin_airport']} ➔ {f['dest_airport']}) - Dep: {f['scheduled_departure']}": f['flight_id']
                    for f in hub_flights
                }
                gate_choice_map = {
                    f"Terminal {g['terminal_number']} • Bay {g['gate_number']} ({g['current_status']})": g['gate_id']
                    for g in local_gates
                }
                
                sel_f_lbl = st.selectbox("Select Flight:", list(flight_choice_map.keys()))
                sel_g_lbl = st.selectbox("Select Target Gate:", list(gate_choice_map.keys()))
                
                f_id = flight_choice_map[sel_f_lbl]
                g_id = gate_choice_map[sel_g_lbl]
                
                c_t1, c_t2 = st.columns(2)
                with c_t1:
                    start_time = st.text_input("Assigned From (YYYY-MM-DD HH:MM:SS):", value="2026-10-30 14:00:00")
                with c_t2:
                    end_time = st.text_input("Assigned Until (YYYY-MM-DD HH:MM:SS):", value="2026-10-30 15:15:00")
                
                assign_status = st.selectbox("Turnaround State:", ["CONFIRMED", "OCCUPIED"])
                assign_btn = st.form_submit_button("Book Gate Assignment", type="primary", use_container_width=True)
                
                if assign_btn:
                    success, msg = db.assign_gate(g_id, f_id, start_time, end_time, status=assign_status)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.warning("Insufficient gates or active flights available for assignment at this hub.")

    with col_del:
        st.markdown("#### 🗑️ Cancel Existing Gate Assignment")
        q_del = """
            SELECT ga.assignment_id, f.flight_number, g.gate_number, g.terminal_number, ga.assigned_from, ga.assigned_until
            FROM GATE_ASSIGNMENT ga
            JOIN GATE g ON ga.gate_id = g.gate_id
            JOIN FLIGHT f ON ga.flight_id = f.flight_id
            WHERE g.airport_code = ?;
        """
        del_assignments = db.run_query(q_del, (selected_code,))
        if del_assignments:
            with st.form("cancel_assignment_form"):
                cancel_opts = {
                    f"Assignment #{a['assignment_id']} • Flight {a['flight_number']} at Gate {a['terminal_number']}-{a['gate_number']} ({a['assigned_from']})": a['assignment_id']
                    for a in del_assignments
                }
                cancel_label = st.selectbox("Select Assignment to Release:", list(cancel_opts.keys()))
                cancel_id = cancel_opts[cancel_label]
                
                del_btn = st.form_submit_button("Release / Cancel Gate", type="secondary", use_container_width=True)
                if del_btn:
                    success, msg = db.cancel_gate_assignment(cancel_id)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"Failed to cancel: {msg}")
        else:
            st.info("No active assignments to cancel at this hub.")

# ---------------------------------------------------------------------
# TAB 5: Operational Reports & Analytics
# ---------------------------------------------------------------------
with tabs[4]:
    st.subheader("Operational Reports & Course Syllabus Demonstrations")
    report_type = st.radio("Select Analytics View:", [
        "1. Runway Congestion by Peak Hour (GROUP BY + HAVING)", 
        "2. Gate Turnaround Duration & Busiest Gates (Subquery + Aggregate AVG)", 
        "3. Network-Wide Aerodrome Health View"
    ], horizontal=True)
    
    if "Runway Congestion" in report_type:
        st.markdown("**Relational Concept:** Multi-table JOIN (`RUNWAY` + `FLIGHT`), `date_trunc('hour')` time slicing, `GROUP BY`, and `HAVING COUNT(*) >= 1`.")
        data_c = db.get_runway_congestion()
        if data_c:
            st.dataframe(pd.DataFrame(data_c), hide_index=True, use_container_width=True)
            
    elif "Gate Turnaround" in report_type:
        st.markdown("**Relational Concept:** Correlated subquery computing per-gate turnaround durations via epoch extraction, joined with physical gate metadata.")
        data_t = db.get_gate_turnaround_stats()
        if data_t:
            st.dataframe(pd.DataFrame(data_t), hide_index=True, use_container_width=True)
            
    elif "Network-Wide" in report_type:
        st.markdown("**Relational Concept:** Reads pre-aggregated view `view_airport_ground_dashboard` across all 12 Indian airport facilities.")
        data_v = db.get_ground_dashboard_view()
        if data_v:
            st.dataframe(pd.DataFrame(data_v), hide_index=True, use_container_width=True)
