import streamlit as st
import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Airport Ground Control | SkyFlow", page_icon="🛫", layout="wide")

# ---------------------------------------------------------------------
# Database Connection Configuration
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("🔌 Database Connection")
    db_host = st.text_input("Host", value="localhost")
    db_port = st.text_input("Port", value="5432")
    db_name = st.text_input("Database", value="skyflow_db")
    db_user = st.text_input("User", value="postgres")
    db_pass = st.text_input("Password", type="password", value="postgres")
    
    conn_params = {
        "host": db_host,
        "port": db_port,
        "dbname": db_name,
        "user": db_user,
        "password": db_pass
    }

def get_connection():
    try:
        conn = psycopg2.connect(**conn_params)
        return conn
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None

def run_query(query, params=None, is_dml=False):
    """Executes a SQL query safely and handles transactions/errors."""
    conn = get_connection()
    if not conn:
        return None
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                if is_dml:
                    conn.commit()
                    return True
                else:
                    return cur.fetchall()
    except psycopg2.Error as err:
        # Display explicit DBMS error for learning and demo evaluation
        st.error(f"⚠️ **DBMS Constraint / Execution Error:**\n\n`{err.pgerror or str(err)}`")
        if err.pgcode:
            st.caption(f"SQLSTATE Code: `{err.pgcode}`")
        return None
    finally:
        conn.close()

# ---------------------------------------------------------------------
# UI Layout
# ---------------------------------------------------------------------
st.title("🛫 Member 1: Airport Ground Control")
st.caption("Ground Infrastructure & Terminal Movement Monitor")

# Fetch all airports
airports_data = run_query("SELECT airport_code, name, city FROM airport ORDER BY airport_code;")
if not airports_data:
    st.warning("Could not load airports. Ensure PostgreSQL is running, `skyflow_db` is created, and `schema_shared.sql` + `seed_member1.sql` have been loaded.")
    st.stop()

airport_dict = {f"{a['airport_code']} - {a['city']} ({a['name']})": a['airport_code'] for a in airports_data}
selected_label = st.selectbox("Select Airport Facility:", list(airport_dict.keys()))
selected_code = airport_dict[selected_label]

tabs = st.tabs([
    "📊 Ground Overview", 
    "🛬 Runways Management", 
    "🚪 Gates Status", 
    "📝 Assign Gate (Add)", 
    "📈 Operational Reports"
])

# ---------------------------------------------------------------------
# TAB 1: Ground Overview
# ---------------------------------------------------------------------
with tabs[0]:
    st.subheader(f"Ground Status Summary: {selected_code}")
    
    view_data = run_query(
        "SELECT * FROM view_airport_ground_dashboard WHERE airport_code = %s;", 
        (selected_code,)
    )
    if view_data:
        v = view_data[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Runways", v['total_runways'])
        c2.metric("Available Runways", v['available_runways'])
        c3.metric("Total Gates", v['total_gates'])
        c4.metric("Free Gates", v['free_gates'])
        
        st.info(f"**Elevation:** {v['elevation_ft']} ft | **City:** {v['city']}")

    st.markdown("#### Active Gate Assignments Today")
    active_assignments = run_query("""
        SELECT 
            ga.assignment_id,
            g.terminal,
            g.gate_number,
            f.flight_number,
            f.origin_airport || ' ➔ ' || f.destination_airport AS route,
            ga.assigned_from,
            ga.assigned_until,
            ga.status
        FROM gate_assignment ga
        JOIN gate g ON ga.gate_id = g.gate_id
        JOIN flight f ON ga.flight_id = f.flight_id
        WHERE g.airport_code = %s
        ORDER BY ga.assigned_from ASC;
    """, (selected_code,))
    
    if active_assignments:
        st.dataframe(pd.DataFrame(active_assignments), use_container_width=True)
    else:
        st.write("No active assignments scheduled for this airport.")

# ---------------------------------------------------------------------
# TAB 2: Runway Management (Read + Update Status)
# ---------------------------------------------------------------------
with tabs[1]:
    st.subheader("Runway Status Grid")
    runways = run_query(
        "SELECT runway_id, runway_designator, length_m, width_m, surface_type, current_status FROM runway WHERE airport_code = %s ORDER BY runway_designator;", 
        (selected_code,)
    )
    
    if runways:
        cols = st.columns(len(runways))
        status_colors = {
            "AVAILABLE": "🟢 #28a745",
            "OCCUPIED": "🟡 #ffc107",
            "CLOSED": "🔴 #dc3545"
        }
        
        for idx, r in enumerate(runways):
            with cols[idx]:
                st.markdown(
                    f"""
                    <div style="border: 2px solid #ddd; border-radius: 8px; padding: 12px; background-color: #fafafa;">
                        <h4 style="margin: 0;">Runway {r['runway_designator']}</h4>
                        <p style="font-size: 13px; color: #555; margin: 4px 0;">{r['length_m']}m × {r['width_m']}m ({r['surface_type']})</p>
                        <h5 style="margin: 6px 0; color: {status_colors[r['current_status']].split()[1]};">
                            {r['current_status']}
                        </h5>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        
        st.markdown("---")
        st.subheader("Update Runway Status")
        with st.form("update_runway_form"):
            selected_r_id = st.selectbox(
                "Select Runway:", 
                options=[r['runway_id'] for r in runways],
                format_func=lambda x: next(f"Runway {r['runway_designator']} (Current: {r['current_status']})" for r in runways if r['runway_id'] == x)
            )
            new_status = st.selectbox("New Operational Status:", ["AVAILABLE", "OCCUPIED", "CLOSED"])
            submit_runway = st.form_submit_button("Update Status")
            
            if submit_runway:
                res = run_query(
                    "UPDATE runway SET current_status = %s WHERE runway_id = %s;", 
                    (new_status, selected_r_id), 
                    is_dml=True
                )
                if res:
                    st.success(f"Runway status successfully updated to {new_status}!")
                    st.rerun()

# ---------------------------------------------------------------------
# TAB 3: Gate Status
# ---------------------------------------------------------------------
with tabs[2]:
    st.subheader("Terminal Gates")
    status_filter = st.radio("Filter By Status:", ["ALL", "AVAILABLE", "OCCUPIED", "MAINTENANCE"], horizontal=True)
    
    gate_query = "SELECT gate_id, terminal, gate_number, gate_type, current_status FROM gate WHERE airport_code = %s"
    params = [selected_code]
    if status_filter != "ALL":
        gate_query += " AND current_status = %s"
        params.append(status_filter)
    gate_query += " ORDER BY terminal, gate_number;"
    
    gates = run_query(gate_query, tuple(params))
    if gates:
        st.dataframe(pd.DataFrame(gates), use_container_width=True)
    else:
        st.info("No gates found matching the filter.")

# ---------------------------------------------------------------------
# TAB 4: Assign Gate Form (Create / Add with Constraint Validation)
# ---------------------------------------------------------------------
with tabs[3]:
    st.subheader("Assign Gate to Flight")
    st.markdown("Creates a new booking in `gate_assignment`. Validates against time constraints and double-booking triggers.")
    
    # Available gates at this airport
    local_gates = run_query("SELECT gate_id, terminal || ' - Gate ' || gate_number AS label FROM gate WHERE airport_code = %s ORDER BY terminal, gate_number;", (selected_code,))
    # Available flights involving this airport
    flights = run_query("""
        SELECT flight_id, flight_number, origin_airport, destination_airport, scheduled_departure 
        FROM flight 
        WHERE (origin_airport = %s OR destination_airport = %s)
          AND current_status NOT IN ('CANCELLED')
        ORDER BY scheduled_departure DESC;
    """, (selected_code, selected_code))
    
    if local_gates and flights:
        with st.form("assign_gate_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                f_choice = st.selectbox(
                    "Select Flight:", 
                    options=[f['flight_id'] for f in flights],
                    format_func=lambda x: next(f"{f['flight_number']} ({f['origin_airport']} ➔ {f['destination_airport']})" for f in flights if f['flight_id'] == x)
                )
                g_choice = st.selectbox(
                    "Select Gate:",
                    options=[g['gate_id'] for g in local_gates],
                    format_func=lambda x: next(g['label'] for g in local_gates if g['gate_id'] == x)
                )
            with col_b:
                start_time = st.text_input("Assigned From (YYYY-MM-DD HH:MM:SS):", value="2026-10-30 14:00:00")
                end_time = st.text_input("Assigned Until (YYYY-MM-DD HH:MM:SS):", value="2026-10-30 15:15:00")
                assign_status = st.selectbox("Initial Status:", ["CONFIRMED", "OCCUPIED"])

            assign_btn = st.form_submit_button("Book Gate Assignment")
            if assign_btn:
                insert_query = """
                    INSERT INTO gate_assignment (gate_id, flight_id, assigned_from, assigned_until, status)
                    VALUES (%s, %s, %s, %s, %s);
                """
                success = run_query(insert_query, (g_choice, f_choice, start_time, end_time, assign_status), is_dml=True)
                if success:
                    st.success("Gate successfully assigned!")
                    st.rerun()

    st.markdown("---")
    st.subheader("Cancel Existing Assignment (DELETE)")
    del_assignments = run_query("""
        SELECT ga.assignment_id, f.flight_number, g.gate_number, ga.assigned_from, ga.assigned_until
        FROM gate_assignment ga
        JOIN gate g ON ga.gate_id = g.gate_id
        JOIN flight f ON ga.flight_id = f.flight_id
        WHERE g.airport_code = %s;
    """, (selected_code,))
    
    if del_assignments:
        with st.form("cancel_assignment_form"):
            cancel_id = st.selectbox(
                "Select Assignment to Cancel:",
                options=[a['assignment_id'] for a in del_assignments],
                format_func=lambda x: next(f"ID #{a['assignment_id']} | Flight {a['flight_number']} at Gate {a['gate_number']} ({a['assigned_from']})" for a in del_assignments if a['assignment_id'] == x)
            )
            del_btn = st.form_submit_button("Delete / Cancel Assignment")
            if del_btn:
                res = run_query("DELETE FROM gate_assignment WHERE assignment_id = %s;", (cancel_id,), is_dml=True)
                if res:
                    st.success(f"Assignment #{cancel_id} removed.")
                    st.rerun()

# ---------------------------------------------------------------------
# TAB 5: Analytical Reports
# ---------------------------------------------------------------------
with tabs[4]:
    st.subheader("📊 Operational Analytics & Reports")
    
    report_type = st.radio("Choose Report:", [
        "1. Runway Congestion (Peak Hour Movements)", 
        "2. Gate Turnaround & Busiest Gates", 
        "3. Network-Wide Ground Dashboard (View)"
    ])
    
    if "Runway Congestion" in report_type:
        st.markdown("**Query Concept:** Groups flights by assigned runway and 1-hour time slices using `date_trunc` with `HAVING COUNT(*) >= 2`.")
        q1 = """
            SELECT 
                r.airport_code,
                r.runway_designator,
                date_trunc('hour', f.scheduled_departure) AS peak_hour_window,
                COUNT(f.flight_id) AS total_scheduled_movements,
                r.current_status AS runway_status
            FROM runway r
            JOIN flight f ON r.runway_id = f.assigned_runway_id
            WHERE f.current_status NOT IN ('CANCELLED', 'DIVERTED')
            GROUP BY r.airport_code, r.runway_designator, date_trunc('hour', f.scheduled_departure), r.current_status
            ORDER BY total_scheduled_movements DESC, peak_hour_window ASC;
        """
        data = run_query(q1)
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
            
    elif "Gate Turnaround" in report_type:
        st.markdown("**Query Concept:** Subquery calculates per-gate aggregates (count, average turnaround in minutes), outer query joins physical gate details.")
        q2 = """
            SELECT 
                g.airport_code,
                g.terminal,
                g.gate_number,
                g.gate_type,
                stats.total_flights_handled,
                ROUND(stats.avg_turnaround_minutes::numeric, 1) AS avg_turnaround_mins,
                stats.min_turnaround_minutes,
                stats.max_turnaround_minutes
            FROM gate g
            JOIN (
                SELECT 
                    gate_id,
                    COUNT(assignment_id) AS total_flights_handled,
                    AVG(EXTRACT(EPOCH FROM (assigned_until - assigned_from)) / 60.0) AS avg_turnaround_minutes,
                    MIN(EXTRACT(EPOCH FROM (assigned_until - assigned_from)) / 60.0) AS min_turnaround_minutes,
                    MAX(EXTRACT(EPOCH FROM (assigned_until - assigned_from)) / 60.0) AS max_turnaround_minutes
                FROM gate_assignment
                WHERE status IN ('COMPLETED', 'OCCUPIED', 'CONFIRMED')
                GROUP BY gate_id
            ) stats ON g.gate_id = stats.gate_id
            ORDER BY stats.total_flights_handled DESC, avg_turnaround_mins DESC;
        """
        data = run_query(q2)
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
            
    elif "Network-Wide" in report_type:
        st.markdown("**Query Concept:** Reads the shared summary view `view_airport_ground_dashboard` across all 12 major Indian airports.")
        q3 = "SELECT * FROM view_airport_ground_dashboard ORDER BY airport_code;"
        data = run_query(q3)
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
